import sqlite3
import streamlit as st  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import ticker  # type: ignore
import pandas as pd

st.set_page_config(page_title="Dataseekr Player Search", page_icon="⚾")
st.title("⚾ Dataseekr Player Search")

# --- Path to your master DB ---
DB_PATH = "statdb.db"
st.write("Database file:", DB_PATH)

# --- Section selection ---
section = st.selectbox("Select section", ["hitting", "pitching", "fielding"])

# --- Player name input ---
player_name = st.text_input("Enter player name (partial or full)")

# --- Map section to table and stats ---
SECTION_MAP = {
    "hitting": {
        "table": "all_hitting_stats",
        "stats": ["ba", "ab", "runs", "hits"]
    },
    "pitching": {
        "table": "all_pitching_stats",
        "stats": ["era", "wl", "ip"]
    },
    "fielding": {
        "table": "all_fielding_stats",
        "stats": ["fld_pct"]
    },
}


def search_and_plot(name: str, section: str):
    table_info = SECTION_MAP[section]
    table = table_info["table"]
    stats = table_info["stats"]

    # --- Query the DB ---
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT name, school, year, {', '.join(stats)}
        FROM {table}
        WHERE LOWER(name) LIKE LOWER(?)
        ORDER BY year
    """
    df = pd.read_sql_query(query, conn, params=(f"%{name}%",))
    conn.close()

    if df.empty:
        st.warning("No matching players found.")
        return

    # --- Display player info ---
    for idx, row in df.iterrows():
        st.subheader(f"{row['name']} ({row['year']})")
        st.write(f"School: {row['school']}")
        stat_text = " | ".join([f"{s.upper()}: {row[s]}" for s in stats])
        st.write(stat_text)
        st.divider()

    # --- Plot each stat separately ---
    for stat in stats:
        if stat not in df.columns:
            continue

        fig, ax = plt.subplots()
        ax.plot(df["year"], df[stat], marker="o")
        ax.set_xlabel("Year")
        ax.set_ylabel(stat.upper())
        ax.set_title(f"{name} - {stat.upper()} ({section.capitalize()})")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(True, linestyle="--", alpha=0.6)
        st.pyplot(fig)


# --- Run search if player name provided ---
if player_name:
    search_and_plot(player_name, section)
