import duckdb
import pandas as pd


def initialize_db():
    conn = duckdb.connect("nyc_analytics.db")

    print("Initializing DuckDB with NYC 311 Data...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nyc_311 AS 
        SELECT * FROM read_csv_auto('nyc_311_sample.csv')
    """)
    print("Database ready.")
    conn.close()


if __name__ == "__main__":
    initialize_db()
