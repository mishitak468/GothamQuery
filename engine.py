import os
import duckdb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class SQLCopilot:
    def __init__(self, db_path="nyc_analytics.db"):
        self.db_path = db_path
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model_id = "llama-3.3-70b-versatile"

        self.schema = """
        Database: DuckDB
        Table name: nyc_311

        Columns — always wrap in double quotes, always use FROM nyc_311:
          "Unique Key"                           BIGINT
          "Created Date"                         TIMESTAMP
          "Closed Date"                          TIMESTAMP
          "Agency"                               VARCHAR   (e.g. 'NYPD', 'HPD', 'DOT', 'DSNY')
          "Agency Name"                          VARCHAR
          "Problem (formerly Complaint Type)"    VARCHAR   (e.g. 'Noise - Residential', 'Street Condition', 'Illegal Parking', 'Pothole', 'Rat Sightings')
          "Problem Detail (formerly Descriptor)" VARCHAR   (detailed description — use for LIKE '%keyword%' searches)
          "Location Type"                        VARCHAR
          "Incident Zip"                         BIGINT    (NULL for some rows)
          "Status"                               VARCHAR   (values: 'Open', 'Closed', 'In Progress', 'Assigned', 'Pending', 'Started')
          "Borough"                              VARCHAR   (values: 'MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND', 'Unspecified')
          "Latitude"                             DOUBLE
          "Longitude"                            DOUBLE

        Data date range: 2026-03-01 to 2026-04-21

        STRICT DuckDB RULES — follow exactly:
          1. EVERY query MUST have FROM nyc_311. Never write SELECT without FROM.
          2. Always wrap column names in double quotes: "Agency" not Agency.
          3. String values are case-sensitive: 'MANHATTAN' not 'Manhattan', 'NYPD' not 'nypd'.
          4. For simple counts use: SELECT count(*) FROM nyc_311 WHERE ...
             NOT: SELECT count(*) FILTER (WHERE ...) — this requires a FROM clause too.
          5. FILTER syntax (only with FROM): SELECT count(*) FILTER (WHERE "Agency"='NYPD') FROM nyc_311
          6. Date truncation: date_trunc('day', "Created Date")
          7. Day of week: EXTRACT(DOW FROM "Created Date") where 0=Sunday, 6=Saturday
          8. No semicolons. No markdown. No explanation. Return ONLY the SQL string.
        """

    def generate_query(self, user_question):
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a DuckDB SQL expert. Given a schema and a question, "
                        "return ONLY the raw SQL query — no markdown, no backticks, "
                        "no explanation, no semicolons. "
                        "CRITICAL: Every SELECT must include FROM nyc_311. "
                        "Always double-quote column names."
                    )
                },
                {
                    "role": "user",
                    "content": f"Schema:\n{self.schema}\n\nQuestion: {user_question}\n\nSQL:"
                }
            ],
            temperature=0,
            max_tokens=512,
        )
        sql = response.choices[0].message.content.strip()
        sql = sql.replace("```sql", "").replace(
            "```", "").replace(";", "").strip()
        return sql

    def execute_query(self, sql):
        conn = duckdb.connect(self.db_path)
        try:
            df = conn.execute(sql).df()
            return df, None
        except Exception as e:
            return None, str(e)
        finally:
            conn.close()
