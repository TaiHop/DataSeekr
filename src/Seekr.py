import sqlite3
import re

import pandas as pd  # type: ignore
import streamlit as st  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import ticker  # type: ignore


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="DataSeekr Player Search",
    page_icon="⚾",
    layout="wide"
)


# ---------------- CLEAN STYLE ----------------
st.markdown("""
<style>
.stApp {
    background-color: #0B1020;
    color: #F9FAFB;
}

.app-title {
    font-size: 42px;
    font-weight: 800;
    color: #FBBF24;
}

.app-subtitle {
    color: #D1D5DB;
    margin-bottom: 20px;
}

.block-card {
    background-color: #111827;
    border: 1px solid #374151;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
}

.stTextInput input {
    background-color: #111827 !important;
    color: white !important;
    border: 1px solid #374151 !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


DB_PATH = "src/statdb.db"


# ---------------- SECTION MAPS ----------------
SECTION_MAP = {
    "Hitting": "hitting_stats",
    "Pitching": "pitching_stats",
    "Fielding": "fielding_stats"
}

SECTION_STATS = {
    "Hitting": ["ba", "ab", "runs", "hits", "rbi"],
    "Pitching": ["era", "ip", "so"],  # wl removed
    "Fielding": ["fld_pct", "total_chances", "errors"]
}


# ---------------- UTIL ----------------
def clean_numeric(series: pd.Series, is_percent=False):
    s = series.astype(str).str.replace(",", "").str.strip()
    if is_percent:
        s = s.str.replace("%", "")
    return pd.to_numeric(s, errors="coerce")


def normalize_name(name):
    name = name.lower().strip()
    name = re.sub(r'\.', '', name)
    parts = name.split()

    if len(parts) >= 2:
        return f"{parts[0][0]} {parts[-1]}"
    return name


# ---------------- DATA ACCESS ----------------
def get_player_data(name: str, section: str):
    table = SECTION_MAP[section]
    search_normalized = normalize_name(name)

    conn = sqlite3.connect(DB_PATH)

    query = f"""
        SELECT *
        FROM {table}
        WHERE LOWER(SUBSTR(name, 1, 1) || ' ' || SUBSTR(name, INSTR(name, ' ') + 1)) = ?
        ORDER BY year
    """

    df = pd.read_sql_query(query, conn, params=(search_normalized,))
    conn.close()

    if not df.empty:
        if "year" in df.columns:
            df["year"] = clean_numeric(df["year"])

        for stat in SECTION_STATS[section]:
            if stat in df.columns:
                df[stat] = clean_numeric(df[stat], is_percent=(stat == "fld_pct"))

    return df


# ---------------- DISPLAY ----------------
def display_player(name: str, section: str):
    df = get_player_data(name, section)

    if df.empty:
        st.warning(f"No data found for player '{name}' in {section}.")
        return

    st.subheader(f"{name} — {section}")

    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.dataframe(df, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Performance Trends")

    cols = st.columns(2)

    for i, stat in enumerate(SECTION_STATS[section]):
        if stat not in df.columns or df[stat].dropna().empty:
            continue

        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.plot(df["year"], df[stat], marker="o")
        ax.set_title(stat.upper())
        ax.set_xlabel("Year")
        ax.set_ylabel(stat.upper())
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(True, linestyle="--", alpha=0.5)

        with cols[i % 2]:
            st.markdown('<div class="block-card">', unsafe_allow_html=True)
            st.pyplot(fig)
            st.markdown('</div>', unsafe_allow_html=True)


# ---------------- COMPARISON ----------------
def compare_players(p1, p2, section, stat):
    df1 = get_player_data(p1, section)
    df2 = get_player_data(p2, section)

    if df1.empty or df2.empty:
        st.warning("One or both players not found.")
        return

    if stat not in df1.columns or stat not in df2.columns:
        st.warning("Stat not available.")
        return

    merged = pd.DataFrame({
        "Year": df1["year"],
        p1: df1[stat]
    }).merge(
        pd.DataFrame({
            "Year": df2["year"],
            p2: df2[stat]
        }),
        on="Year",
        how="outer"
    ).sort_values("Year")

    st.subheader(f"{p1} vs {p2} — {stat.upper()}")

    st.dataframe(merged, width="stretch")

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(merged["Year"], merged[p1], marker="o", label=p1)
    ax.plot(merged["Year"], merged[p2], marker="o", label=p2)
    ax.legend()
    ax.set_title(stat.upper())
    ax.grid(True, linestyle="--", alpha=0.5)

    st.pyplot(fig)


# ---------------- HEADER ----------------
st.markdown('<div class="app-title">⚾ DataSeekr</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Search and compare PAC player stats</div>', unsafe_allow_html=True)


# ---------------- UI ----------------
tab1, tab2 = st.tabs(["Search", "Compare"])

with tab1:
    name = st.text_input("Player Name")
    sections = st.multiselect("Section", list(SECTION_MAP.keys()), default=list(SECTION_MAP.keys()))

    if name:
        for sec in sections:
            display_player(name, sec)

with tab2:
    p1 = st.text_input("Player 1")
    p2 = st.text_input("Player 2")
    sec = st.selectbox("Section", list(SECTION_MAP.keys()))
    stat = st.selectbox("Stat", SECTION_STATS[sec])

    if p1 and p2:
        compare_players(p1, p2, sec, stat)
