import sqlite3
import pandas as pd  # type: ignore
import streamlit as st  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import ticker  # type: ignore
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Dataseekr Player Search",
    page_icon="⚾",
    layout="wide"
)

# ---------------- CUSTOM STYLING ----------------
st.markdown("""
    <style>
        .chart-container {
            border: 2px solid white;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            background-color: #111111;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.title("⚾ Dataseekr")
st.caption("Search player stats across hitting, pitching, and fielding")

DB_PATH = "statdb.db"

# ---------------- SECTION MAPS ----------------
SECTION_MAP = {
    "Hitting": "hitting_stats",
    "Pitching": "pitching_stats",
    "Fielding": "fielding_stats"
}

SECTION_STATS = {
    "Hitting": ["ba", "ab", "runs", "hits", "rbi"],
    "Pitching": ["era", "wl", "ip", "so"],
    "Fielding": ["fld_pct", "total_chances", "errors"]
}

# ---------------- UTIL ----------------


def clean_numeric(series: pd.Series, is_percent=False):
    s = series.astype(str).str.replace(",", "").str.strip()
    if is_percent:
        s = s.str.replace("%", "")
    return pd.to_numeric(s, errors="coerce")


def normalize_name(name):
    name = name.lower()
    name = re.sub(r'\.', '', name)
    parts = name.split()
    if len(parts) >= 2:
        first_initial = parts[0][0]
        last = parts[-1]
        return f"{first_initial} {last}"
    return name


# ---------------- DATABASE INITIALIZATION (RUN ONCE) ----------------
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for table in SECTION_MAP.values():

        # Check if canonical_name exists
        cur.execute(f"PRAGMA table_info({table})")
        cols = [col[1] for col in cur.fetchall()]

        if "canonical_name" not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN canonical_name TEXT;")

        # Bulk update only NULL rows
        cur.execute(f"""
            UPDATE {table}
            SET canonical_name =
                LOWER(SUBSTR(name, 1, 1) || ' ' ||
                SUBSTR(name, INSTR(name, ' ') + 1))
            WHERE canonical_name IS NULL
        """)

    conn.commit()
    conn.close()


# Run once when app loads
initialize_database()


# ---------------- SEARCH FUNCTION ----------------
def search_and_plot(name: str, section: str):

    table = SECTION_MAP[section]
    stats_to_plot = SECTION_STATS[section]

    conn = sqlite3.connect(DB_PATH)

    search_normalized = normalize_name(name)

    query = f"""
        SELECT *
        FROM {table}
        WHERE canonical_name = ?
        ORDER BY year
    """

    df = pd.read_sql_query(query, conn, params=(search_normalized,))
    conn.close()

    if df.empty:
        st.warning(f"No data found for player '{name}' in {section}.")
        return

    st.subheader(f"{name} — {section}")
    st.dataframe(df, width=1200)

    # Clean numeric columns
    for stat in stats_to_plot:
        if stat in df.columns:
            df[stat] = clean_numeric(df[stat], is_percent=(stat == "fld_pct"))

    df["year"] = clean_numeric(df["year"])

    # -------- SMALL INDIVIDUAL GRAPHS --------
    st.markdown("## 📊 Performance Trends")

    cols = st.columns(2)

    for i, stat in enumerate(stats_to_plot):
        if stat not in df.columns or df[stat].dropna().empty:
            continue

        fig, ax = plt.subplots(figsize=(5, 2.5))

        ax.plot(df["year"], df[stat], marker="o")
        ax.set_xlabel("Year", fontsize=8)
        ax.set_ylabel(stat.upper(), fontsize=8)
        ax.set_title(stat.upper(), fontsize=10)
        ax.tick_params(axis='both', labelsize=7)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(True, linestyle="--", alpha=0.5)

        with cols[i % 2]:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.pyplot(fig)
            st.markdown('</div>', unsafe_allow_html=True)


# ---------------- STREAMLIT UI ----------------

col1, col2 = st.columns([2, 1])

with col1:
    player_name = st.text_input(
        "Player Name",
        placeholder="Enter player name..."
    )

with col2:
    sections = st.multiselect(
        "Section",
        options=list(SECTION_MAP.keys()),
        default=list(SECTION_MAP.keys())
    )

if player_name and sections:
    for sec in sections:
        search_and_plot(player_name, sec)
