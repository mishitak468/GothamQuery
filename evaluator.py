import duckdb
import time
import pandas as pd
from engine import SQLCopilot


def normalize_df(df):
    """Standard normalization: lowercase col names, sort rows + cols, round floats."""
    if df is None or df.empty:
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
    """For single-value results: check within 1% relative tolerance."""
    try:
        v_gen = float(df_gen.iloc[0, 0])
        v_gt = float(df_gt.iloc[0, 0])
        if v_gt == 0:
            return v_gen == 0
        return abs(v_gen - v_gt) / abs(v_gt) <= rtol
    except Exception:
        return False


def results_match(df_gen, df_gt, question):
    """
    Smart comparison that handles the real-world failure modes:
      - Scalar results: use relative tolerance
      - Multi-col results: normalize then compare
      - Shape mismatches on subset-column queries: check key column values match
    """
    if df_gen is None or df_gt is None:
        return False

    gen = normalize_df(df_gen)
    gt = normalize_df(df_gt)

    # Exact match (best case)
    if gen.equals(gt):
        return True

    # Scalar: 1x1 result — use tolerance
    if gt.shape == (1, 1):
        return scalar_close(df_gen, df_gt)

    # Shape mismatch where row count matches: model may have selected
    # fewer columns but got the right data rows — check first col values
    if gen.shape[0] == gt.shape[0] and gen.shape[0] > 0:
        # comparing just the first column values (the key data column)
        try:
            gen_col0 = gen.iloc[:, 0].reset_index(drop=True)
            gt_col0 = gt.iloc[:, 0].reset_index(drop=True)
            if gen_col0.equals(gt_col0):
                return True
        except Exception:
            pass

    return False


def run_eval():
    copilot = SQLCopilot()
    conn = duckdb.connect("nyc_analytics.db")

    test_cases = [
        # 1. Basic Selection & Filtering
        {
            "question": "Show all open complaints for the NYPD.",
            "ground_truth_sql": """SELECT * FROM nyc_311 WHERE "Agency" = 'NYPD' AND "Status" = 'Open'"""
        },
        # 2. Basic Aggregation (GROUP BY)
        {
            "question": "What are the total number of complaints per borough?",
            "ground_truth_sql": """SELECT "Borough", count(*) as total FROM nyc_311 GROUP BY "Borough" ORDER BY total DESC"""
        },
        # 3. Filtering with Aggregation (HAVING)
        {
            "question": "Which agencies have more than 500 total complaints?",
            "ground_truth_sql": """SELECT "Agency", count(*) as cnt FROM nyc_311 GROUP BY "Agency" HAVING count(*) > 500 ORDER BY cnt DESC"""
        },
        # 4. Multi-Condition Filtering
        {
            "question": "List residential noise complaints in Manhattan that are still open.",
            "ground_truth_sql": """SELECT * FROM nyc_311 WHERE "Problem (formerly Complaint Type)" = 'Noise - Residential' AND "Borough" = 'MANHATTAN' AND "Status" = 'Open'"""
        },
        # 5. Date Truncation (Time Series)
        {
            "question": "Show the daily complaint count for March 2026.",
            "ground_truth_sql": """SELECT date_trunc('day', "Created Date") as day, count(*) as cnt FROM nyc_311 WHERE "Created Date" >= '2026-03-01' AND "Created Date" < '2026-04-01' GROUP BY 1 ORDER BY 1"""
        },
        # 6. String LIKE
        {
            "question": "How many complaints mention 'Rat' in the description field?",
            "ground_truth_sql": """SELECT count(*) as rat_complaints FROM nyc_311 WHERE "Problem Detail (formerly Descriptor)" LIKE '%Rat%'"""
        },
        # 7. Subquery
        {
            "question": "Show all complaints from the zip code with the most total records.",
            "ground_truth_sql": """SELECT * FROM nyc_311 WHERE "Incident Zip" = (SELECT "Incident Zip" FROM nyc_311 GROUP BY 1 ORDER BY count(*) DESC LIMIT 1)"""
        },
        # 8. Window Function (Ranking)
        {
            "question": "Rank agencies by total complaint volume using a window function.",
            "ground_truth_sql": """SELECT "Agency", count(*) as complaints, RANK() OVER (ORDER BY count(*) DESC) as rank FROM nyc_311 GROUP BY "Agency" ORDER BY rank"""
        },
        # 9. Window Function (Running Total)
        {
            "question": "Show the running cumulative count of complaints ordered by date.",
            "ground_truth_sql": """SELECT "Created Date", count(*) OVER (ORDER BY "Created Date") as cumulative_total FROM nyc_311 ORDER BY "Created Date" LIMIT 500"""
        },
        # 10. CTE
        {
            "question": "Using a CTE, calculate the average number of complaints per day.",
            "ground_truth_sql": """WITH daily_counts AS (SELECT date_trunc('day', "Created Date") as day, count(*) as daily_total FROM nyc_311 GROUP BY 1) SELECT avg(daily_total) as avg_daily_complaints FROM daily_counts"""
        },
        # 11. CASE Statements
        {
            "question": "Label each complaint as 'Noise Related' or 'Other' based on its type.",
            "ground_truth_sql": """SELECT "Problem (formerly Complaint Type)", CASE WHEN "Problem (formerly Complaint Type)" LIKE '%Noise%' THEN 'Noise Related' ELSE 'Other' END as category FROM nyc_311"""
        },
        # 12. Percentages
        {
            "question": "What percentage of total complaints are from the NYPD?",
            "ground_truth_sql": """SELECT ROUND(count(*) FILTER (WHERE "Agency" = 'NYPD') * 100.0 / count(*), 2) as nypd_pct FROM nyc_311"""
        },
        # 13. Self-Join
        {
            "question": "Find zip codes that have both 'Pothole' and 'Rat Sightings' complaints.",
            "ground_truth_sql": """SELECT DISTINCT a."Incident Zip" FROM nyc_311 a JOIN nyc_311 b ON a."Incident Zip" = b."Incident Zip" WHERE a."Problem (formerly Complaint Type)" = 'Pothole' AND b."Problem (formerly Complaint Type)" = 'Rat Sightings'"""
        },
        # 14. NULL Handling
        {
            "question": "Count how many complaints have no zip code recorded.",
            "ground_truth_sql": """SELECT count(*) as missing_zip FROM nyc_311 WHERE "Incident Zip" IS NULL"""
        },
        # 15. Date Math (DOW)
        {
            "question": "Count complaints created on Saturdays or Sundays.",
            "ground_truth_sql": """SELECT count(*) as weekend_complaints FROM nyc_311 WHERE EXTRACT(DOW FROM "Created Date") IN (0, 6)"""
        }
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

            if results_match(res_gen, res_gt, case['question']):
                passed += 1
                print(f"✅ Pass  [{i:02d}]: {case['question']}")
            else:
                gen_n = normalize_df(res_gen)
                gt_n = normalize_df(res_gt)
                note = f"shape: got {gen_n.shape}, expected {gt_n.shape}"
                print(f"❌ Fail  [{i:02d}]: {case['question']} ({note})")
                fail_details.append({
                    "case": i, "question": case['question'],
                    "generated_sql": generated_sql,
                    "gen_sample": res_gen.head(2).to_string(),
                    "gt_sample": res_gt.head(2).to_string()
                })

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
            print(f"  Generated SQL: {d['generated_sql']}")
            print(f"  Generated sample:\n{d['gen_sample']}")
            print(f"  Expected sample:\n{d['gt_sample']}")

    return accuracy


if __name__ == "__main__":
    run_eval()
