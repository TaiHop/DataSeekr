from sqlalchemy import create_engine, text  # type: ignore
import pandas as pd  # type: ignore
import re


def safe_table_name(name: str) -> str:
    """
    SQLite table names cannot start with a number or contain special chars.
    """
    name = name.lower().replace(".csv", "")
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name[0].isdigit():
        name = f"t_{name}"
    return name


def csv_to_db(csv_file: str, table_name: str, db_path: str = "db/bb_stats.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    df = pd.read_csv(csv_file)

    # Normalize column names
    df.columns = df.columns.str.lower()

    # Force the schema we support
    expected_columns = ["name", "school", "ba", "era", "year"]
    df = df[[c for c in expected_columns if c in df.columns]]

    # Ensure required columns exist
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None

    # Type safety
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["ba"] = pd.to_numeric(df["ba"], errors="coerce")
    df["era"] = pd.to_numeric(df["era"], errors="coerce")

    # Remove exact duplicate stat rows
    df = df.drop_duplicates(subset=expected_columns)

    table_name = safe_table_name(table_name)

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                school TEXT,
                ba REAL,
                era REAL,
                year INTEGER
            );
        """))

        df.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False,
            method="multi"
        )

    print(f"📦 Loaded {csv_file} → '{table_name}' ({len(df)} rows)")
