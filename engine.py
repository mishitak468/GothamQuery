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

        # CRITICAL: Use actual column names from the DB (with spaces, quoted)
        self.schema = """
        Database: DuckDB
        Table: nyc_311

        Columns (use EXACTLY these names, always wrapped in double quotes):
          "Unique Key"                           BIGINT
          "Created Date"                         TIMESTAMP
          "Closed Date"                          TIMESTAMP
          "Agency"                               VARCHAR   (e.g. 'NYPD', 'HPD', 'DOT', 'DSNY')
          "Agency Name"                          VARCHAR   (full name, e.g. 'Department of Transportation')
          "Problem (formerly Complaint Type)"    VARCHAR   (e.g. 'Noise - Residential', 'Street Condition', 'Illegal Parking')
          "Problem Detail (formerly Descriptor)" VARCHAR   (detailed description, use for LIKE searches)
          "Location Type"                        VARCHAR
          "Incident Zip"                         BIGINT    (NULL for ~6807 rows)
          "Status"                               VARCHAR   (values: 'Open', 'Closed', 'In Progress', 'Assigned', 'Pending', 'Started', 'Unspecified')
          "Borough"                              VARCHAR   (values: 'MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND', 'Unspecified')
          "Latitude"                             DOUBLE
          "Longitude"                            DOUBLE

        Data date range: 2026-03-01 to 2026-04-21 (NOT 2025 data)
        Total rows: ~534,000

        DuckDB-specific rules:
          - Always wrap column names in double quotes: "Created Date" not created_date
          - Date functions: date_trunc('day', "Created Date"), EXTRACT(DOW FROM "Created Date")
          - DOW: 0=Sunday, 6=Saturday
          - FILTER syntax: count(*) FILTER (WHERE "Agency" = 'NYPD')
          - No semicolons at end
          - String values are case-sensitive: use 'MANHATTAN' not 'Manhattan'
        """

    def generate_query(self, user_question):
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a DuckDB SQL expert. Given a schema and a question, "
                        "return ONLY the raw SQL query. "
                        "No markdown, no backticks, no explanation, no semicolons. "
                        "Always wrap column names in double quotes since they contain spaces."
                    )
                },
                {
                    "role": "user",
                    "content": f"Schema:\n{self.schema}\n\nQuestion: {user_question}"
                }
            ],
            temperature=0,
            max_tokens=512,
        )
        sql = response.choices[0].message.content.strip()
        # Safety cleanup
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
