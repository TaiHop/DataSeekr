import sqlite3
import pandas as pd  # type: ignore
import os   # type: ignore

# Database will be created in the project folder
DB_NAME = "statdb.db"


def csv_to_master_db(csv_file: str, section: str):
    """
    Load CSV data into the master database.
    Automatically creates the table if it doesn't exist.
    All CSV columns are added as table columns dynamically.
    """
    df = pd.read_csv(csv_file)

    # Lowercase all columns for consistency
    df.columns = df.columns.str.lower()

    # Ensure 'year' column exists
    # if "year" not in df.columns:
    #     df["year"] = 2025  # default year

    # Connect to local database in project folder
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Table name per section
    table_name = f"{section}_stats"

    # Dynamically create table columns from CSV
    columns = df.columns.tolist()
    col_defs = ", ".join([f"{col} TEXT" for col in columns if col != "id"])

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {col_defs}
    );
    """
    cur.execute(create_sql)

    # Insert CSV data into table
    df.to_sql(table_name, conn, if_exists="append", index=False)

    conn.commit()
    conn.close()

    print(f"📦 Loaded {csv_file} → '{table_name}' ({len(df)} rows)")
