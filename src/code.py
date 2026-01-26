import sqlite3
import pandas as pd  # type: ignore
import os  # type: ignore

DB_NAME = "statdb.db"


def csv_to_master_db(csv_file: str, section: str):
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.lower()

    if "year" not in df.columns:
        raise ValueError("CSV must include a 'year' column")

    # ---- 🔑 derive school if not in CSV ----
    if "school" in df.columns:
        schools = df["school"].astype(str).unique().tolist()
    else:
        # filename: 2025_wj_hitting.csv → wj
        base = os.path.basename(csv_file)
        school_code = base.split("_")[1]
        schools = [school_code]

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    table_name = f"{section}_stats"

    columns = df.columns.tolist()
    col_defs = ", ".join([f"{col} TEXT" for col in columns if col != "id"])

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {col_defs}
    );
    """
    cur.execute(create_sql)

    # ---- 🔑 delete ONLY this school + year ----
    years = df["year"].astype(str).unique().tolist()
    for year in years:
        for school in schools:
            cur.execute(
                f"DELETE FROM {table_name} WHERE year = ? AND school = ?",
                (year, school),
            )

    df.to_sql(table_name, conn, if_exists="append", index=False)

    conn.commit()
    conn.close()

    print(f"📦 Loaded {csv_file} → '{table_name}' ({len(df)} rows)")
