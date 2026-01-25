import sqlite3
import pandas as pd  # type: ignore
import streamlit as st  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import ticker  # type: ignore

st.set_page_config(page_title="Dataseekr Player Search", page_icon="⚾")
st.title("⚾ Dataseekr Player Search")

DB_PATH = "statdb.db"
st.write("Database file:", DB_PATH)

# Map sections to DB tables
SECTION_MAP = {
    "Hitting": "hitting_stats",
    "Pitching": "pitching_stats",
    "Fielding": "fielding_stats"
}

# Stats to plot per section
SECTION_STATS = {
    "Hitting": ["ba", "ab", "runs", "hits"],
    "Pitching": ["era", "wl", "ip"],
    "Fielding": ["fld_pct", "total_chances", "errors"]
}


def clean_numeric(series: pd.Series, is_percent=False):
    """Convert a pandas series to numeric, handling strings and percentages."""
    s = series.astype(str).str.replace(",", "").str.strip()
    if is_percent:
        s = s.str.replace("%", "")
    return pd.to_numeric(s, errors="coerce")


def search_and_plot(name: str, section: str):
    table = SECTION_MAP[section]
    stats_to_plot = SECTION_STATS[section]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Ensure canonical_name exists
    cur.execute(f"PRAGMA table_info({table})")
    cols = [col[1] for col in cur.fetchall()]
    if "canonical_name" not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN canonical_name TEXT;")
        rows = cur.execute(f"SELECT id, name FROM {table}").fetchall()
        for row_id, name_val in rows:
            parts = name_val.split()
            if len(parts) == 2:
                first, last = parts
                canonical = f"{first} {last}"
            else:
                canonical = name_val
            cur.execute(f"UPDATE {table} SET canonical_name=? WHERE id=?", (canonical, row_id))
        conn.commit()

    # Search: check both "First Last" and "Last First"
    parts = name.split()
    if len(parts) == 2:
        search_names = [name.lower(), f"{parts[1]} {parts[0]}".lower()]
        placeholders = ", ".join(["?"] * len(search_names))
        query = f"SELECT * FROM {table} WHERE LOWER(canonical_name) IN ({placeholders}) ORDER BY year"
        df = pd.read_sql_query(query, conn, params=search_names)
    else:
        query = f"SELECT * FROM {table} WHERE LOWER(canonical_name) LIKE ? ORDER BY year"
        df = pd.read_sql_query(query, conn, params=(f"%{name.lower()}%",))

    conn.close()

    if df.empty:
        st.warning(f"No data found for player '{name}' in {section}.")
        return

    st.subheader(f"{name} - {section}")
    st.dataframe(df)

    # Clean numeric columns
    for stat in stats_to_plot:
        if stat in df.columns:
            df[stat] = clean_numeric(df[stat], is_percent=(stat == "fld_pct"))

    df["year"] = clean_numeric(df["year"])

    # Plot all stats for the section
    for stat in stats_to_plot:
        if stat not in df.columns or df[stat].dropna().empty:
            continue

        fig, ax = plt.subplots()
        ax.plot(df["year"], df[stat], marker="o", linestyle="-")
        ax.set_xlabel("Year")
        ax.set_ylabel(stat.upper())
        ax.set_title(f"{stat.upper()} over years")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(True, linestyle="--", alpha=0.6)
        st.pyplot(fig)


# --- Streamlit UI ---
player_name = st.text_input("Enter player name")
section = st.selectbox("Select section", options=list(SECTION_MAP.keys()))

if player_name and section:
    search_and_plot(player_name, section)
