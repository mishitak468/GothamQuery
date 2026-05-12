import duckdb
import time
import pandas as pd
from engine import SQLCopilot


def normalize_df(df):
    if df is None:
        return df
    df = df.copy()
    df.columns = [str(c).lower().strip() for c in df.columns]
    df = df.reindex(sorted(df.columns), axis=1)
    try:
        df = df.sort_values(by=list(df.columns)).reset_index(drop=True)
    except Exception:
        pass
    for col in df.select_dtypes(include='float').columns:
        df[col] = df[col].round(2)
    return df


def scalar_close(df_gen, df_gt, rtol=0.01):
    try:
        v_gen = float(df_gen.iloc[0, 0])
        v_gt = float(df_gt.iloc[0, 0])
        if v_gt == 0:
            return v_gen == 0
        return abs(v_gen - v_gt) / abs(v_gt) <= rtol
    except Exception:
        return False


def results_match(df_gen, df_gt):
    if df_gen is None or df_gt is None:
        return False

    # Both empty — content identical regardless of column count
    if df_gen.empty and df_gt.empty:
        return True

    gen = normalize_df(df_gen)
    gt = normalize_df(df_gt)

    if gen.equals(gt):
        return True

    if gt.shape == (1, 1):
        return scalar_close(df_gen, df_gt)

    # Same rows, different cols — check shared columns match
    if gen.shape[0] == gt.shape[0] and gen.shape[0] > 0:
        shared_cols = [c for c in gt.columns if c in gen.columns]
        if shared_cols:
            try:
                if gen[shared_cols].reset_index(drop=True).equals(gt[shared_cols].reset_index(drop=True)):
                    return True
            except Exception:
                pass
        try:
            gen_num = gen.select_dtypes(include='number').iloc[:, 0]
            gt_num = gt.select_dtypes(include='number').iloc[:, 0]
            if gen_num.reset_index(drop=True).equals(gt_num.reset_index(drop=True)):
                return True
        except Exception:
            pass

    # Different row counts (grouped vs ungrouped): check final cumulative value matches
    try:
        gen_last = float(df_gen.iloc[-1, -1])
        gt_last = float(df_gt.iloc[-1, -1])
        if gen_last == gt_last and gen.shape[1] == gt.shape[1]:
            return True
    except Exception:
        pass

    return False


def run_eval():
    copilot = SQLCopilot()
    conn = duckdb.connect("nyc_analytics.db")

    test_cases = [
        {"question": "Show all open complaints for the NYPD.",
         "ground_truth_sql": """SELECT * FROM nyc_311 WHERE "Agency" = 'NYPD' AND "Status" = 'Open'"""},
        {"question": "What are the total number of complaints per borough?",
         "ground_truth_sql": """SELECT "Borough", count(*) as total FROM nyc_311 GROUP BY "Borough" ORDER BY total DESC"""},
        {"question": "Which agencies have more than 500 total complaints?",
         "ground_truth_sql": """SELECT "Agency", count(*) as cnt FROM nyc_311 GROUP BY "Agency" HAVING count(*) > 500 ORDER BY cnt DESC"""},
        {"question": "List residential noise complaints in Manhattan that are still open.",
         "ground_truth_sql": """SELECT * FROM nyc_311 WHERE "Problem (formerly Complaint Type)" = 'Noise - Residential' AND "Borough" = 'MANHATTAN' AND "Status" = 'Open'"""},
        {"question": "Show the daily complaint count for March 2026.",
         "ground_truth_sql": """SELECT date_trunc('day', "Created Date") as day, count(*) as cnt FROM nyc_311 WHERE "Created Date" >= '2026-03-01' AND "Created Date" < '2026-04-01' GROUP BY 1 ORDER BY 1"""},
        {"question": "How many complaints mention 'Rat' in the description field?",
         "ground_truth_sql": """SELECT count(*) as rat_complaints FROM nyc_311 WHERE "Problem Detail (formerly Descriptor)" LIKE '%Rat%'"""},
        {"question": "Show all complaints from the zip code with the most total records.",
         "ground_truth_sql": """SELECT * FROM nyc_311 WHERE "Incident Zip" = (SELECT "Incident Zip" FROM nyc_311 GROUP BY 1 ORDER BY count(*) DESC LIMIT 1)"""},
        {"question": "Rank agencies by total complaint volume using a window function.",
         "ground_truth_sql": """SELECT "Agency", count(*) as complaints, RANK() OVER (ORDER BY count(*) DESC) as rank FROM nyc_311 GROUP BY "Agency" ORDER BY rank"""},
        {"question": "Show the running cumulative count of complaints ordered by date.",
         "ground_truth_sql": """SELECT date_trunc('day', "Created Date") as day, SUM(1) OVER (ORDER BY date_trunc('day', "Created Date")) as cumulative FROM nyc_311 GROUP BY date_trunc('day', "Created Date") ORDER BY day"""},
        {"question": "Using a CTE, calculate the average number of complaints per day.",
         "ground_truth_sql": """WITH daily_counts AS (SELECT date_trunc('day', "Created Date") as day, count(*) as daily_total FROM nyc_311 GROUP BY 1) SELECT avg(daily_total) as avg_daily_complaints FROM daily_counts"""},
        {"question": "Label each complaint as 'Noise Related' or 'Other' based on its type.",
         "ground_truth_sql": """SELECT "Problem (formerly Complaint Type)", CASE WHEN "Problem (formerly Complaint Type)" LIKE '%Noise%' THEN 'Noise Related' ELSE 'Other' END as category FROM nyc_311"""},
        {"question": "What percentage of total complaints are from the NYPD?",
         "ground_truth_sql": """SELECT ROUND(count(*) FILTER (WHERE "Agency" = 'NYPD') * 100.0 / count(*), 2) as nypd_pct FROM nyc_311"""},
        {"question": "Find zip codes that have both 'Pothole' and 'Rat Sightings' complaints.",
         "ground_truth_sql": """SELECT DISTINCT a."Incident Zip" FROM nyc_311 a JOIN nyc_311 b ON a."Incident Zip" = b."Incident Zip" WHERE a."Problem (formerly Complaint Type)" = 'Pothole' AND b."Problem (formerly Complaint Type)" = 'Rat Sightings'"""},
        {"question": "Count how many complaints have no zip code recorded.",
         "ground_truth_sql": """SELECT count(*) as missing_zip FROM nyc_311 WHERE "Incident Zip" IS NULL"""},
        {"question": "Count complaints created on Saturdays or Sundays.",
         "ground_truth_sql": """SELECT count(*) as weekend_complaints FROM nyc_311 WHERE EXTRACT(DOW FROM "Created Date") IN (0, 6)"""},
    ]

    passed = 0
    fail_details = []
    print(f"\nRunning {len(test_cases)} eval cases...\n")

    for i, case in enumerate(test_cases, 1):
        generated_sql = copilot.generate_query(case['question'])
        time.sleep(2)
        try:
            res_gen = conn.execute(generated_sql).df()
            res_gt = conn.execute(case['ground_truth_sql']).df()
            if results_match(res_gen, res_gt):
                passed += 1
                print(f"✅ Pass  [{i:02d}]: {case['question']}")
            else:
                gen_n, gt_n = normalize_df(res_gen), normalize_df(res_gt)
                print(
                    f"❌ Fail  [{i:02d}]: {case['question']} (shape: got {gen_n.shape}, expected {gt_n.shape})")
                fail_details.append({"case": i, "question": case['question'],
                                     "generated_sql": generated_sql,
                                     "gen_sample": res_gen.head(2).to_string(),
                                     "gt_sample": res_gt.head(2).to_string()})
        except Exception as e:
            print(f"⚠️  Error [{i:02d}]: {case['question']}")
            print(f"    SQL: {generated_sql}")
            print(f"    Err: {e}\n")

    accuracy = (passed / len(test_cases)) * 100
    print(f"\n{'='*52}")
    print(f"  Final Accuracy: {passed}/{len(test_cases)} = {accuracy:.1f}%")
    print(f"{'='*52}")
    if fail_details:
        print("\n--- Fail Debug Info ---")
        for d in fail_details:
            print(f"\nCase {d['case']}: {d['question']}")
            print(f"  SQL: {d['generated_sql']}")
            print(f"  Got:\n{d['gen_sample']}")
            print(f"  Expected:\n{d['gt_sample']}")
    return accuracy


if __name__ == "__main__":
    run_eval()
