import os
import re
import sqlite3

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
    "Pitching": ["era", "ip", "so"],
    "Fielding": ["fld_pct", "total_chances", "errors"]
}

STAT_LABELS = {
    "ba": "Batting Average",
    "ab": "At Bats",
    "runs": "Runs",
    "hits": "Hits",
    "rbi": "RBI",
    "era": "ERA",
    "ip": "Innings Pitched",
    "so": "Strikeouts",
    "fld_pct": "Fielding %",
    "total_chances": "Total Chances",
    "errors": "Errors"
}


# ---------------- DB CHECK ----------------
if not os.path.exists(DB_PATH):
    st.error(f"Database not found at: {DB_PATH}")
    st.stop()


# ---------------- UTIL ----------------
def clean_numeric(series: pd.Series, is_percent=False):
    s = series.astype(str).str.replace(",", "", regex=False).str.strip()
    if is_percent:
        s = s.str.replace("%", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def normalize_name(name):
    name = str(name).lower().strip()
    name = re.sub(r"\.", "", name)
    name = re.sub(r"\s+", " ", name)
    parts = name.split()

    if len(parts) >= 2:
        return f"{parts[0][0]} {parts[-1]}"
    return name


def pretty_stat_name(stat):
    return STAT_LABELS.get(stat, stat.upper())


def format_value(value, stat):
    if pd.isna(value):
        return ""

    if stat in {"ba", "fld_pct"}:
        return f"{value:.3f}".lstrip("0")

    if stat == "era":
        return f"{value:.2f}"

    if stat == "ip":
        return f"{value:.1f}"

    try:
        return str(int(value))
    except Exception:
        return str(value)


def style_graph(fig, ax, title, xlabel="Year", ylabel=""):
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#111827")

    ax.set_title(title, color="#FBBF24", fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel(xlabel, color="#D1D5DB", fontsize=10, labelpad=8)
    ax.set_ylabel(ylabel, color="#D1D5DB", fontsize=10, labelpad=8)

    ax.tick_params(axis="x", colors="#D1D5DB", labelsize=9)
    ax.tick_params(axis="y", colors="#D1D5DB", labelsize=9)

    ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.25)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#4B5563")
    ax.spines["bottom"].set_color("#4B5563")

    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()


def add_point_labels(ax, x_values, y_values, stat):
    for x, y in zip(x_values, y_values):
        if pd.isna(y):
            continue

        ax.annotate(
            format_value(y, stat),
            (x, y),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
            color="#F9FAFB",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="#0B1020",
                edgecolor="#374151",
                alpha=0.9
            )
        )


def add_y_padding(ax, values):
    clean = pd.Series(values).dropna()

    if clean.empty:
        return

    min_val = clean.min()
    max_val = clean.max()

    if min_val == max_val:
        padding = abs(max_val) * 0.15 if max_val != 0 else 1
    else:
        padding = (max_val - min_val) * 0.18

    ax.set_ylim(min_val - padding, max_val + padding)


# ---------------- DATA ACCESS ----------------
@st.cache_data(show_spinner=False)
def load_section_data(section: str):
    table = SECTION_MAP[section]

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)

    df.columns = df.columns.str.lower()

    if df.empty:
        return df

    if "year" in df.columns:
        df["year"] = clean_numeric(df["year"])

    for stat in SECTION_STATS[section]:
        if stat in df.columns:
            df[stat] = clean_numeric(df[stat], is_percent=(stat == "fld_pct"))

    if "name" in df.columns:
        df["_name_key"] = df["name"].apply(normalize_name)

    return df


def get_player_data(name: str, section: str):
    df = load_section_data(section)

    if df.empty or "_name_key" not in df.columns:
        return pd.DataFrame()

    search_normalized = normalize_name(name)
    result = df[df["_name_key"] == search_normalized].copy()

    if "_name_key" in result.columns:
        result = result.drop(columns=["_name_key"])

    if "year" in result.columns:
        result = result.sort_values("year")

    return result


# ---------------- DISPLAY ----------------
def display_player(name: str, section: str):
    df = get_player_data(name, section)

    if df.empty:
        st.warning(f"No data found for player '{name}' in {section}.")
        return

    st.subheader(f"{name} — {section}")

    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Performance Trends")

    if "year" not in df.columns:
        st.warning("No year column found.")
        return

    cols = st.columns(2)

    for i, stat in enumerate(SECTION_STATS[section]):
        if stat not in df.columns or df[stat].dropna().empty:
            continue

        chart_df = df[["year", stat]].dropna().sort_values("year")

        fig, ax = plt.subplots(figsize=(6.4, 3.4))

        ax.plot(
            chart_df["year"],
            chart_df[stat],
            marker="o",
            linewidth=2.5,
            markersize=7,
            color="#FBBF24",
            markerfacecolor="#FCD34D",
            markeredgecolor="#111827",
            markeredgewidth=1.5
        )

        ax.fill_between(
            chart_df["year"],
            chart_df[stat],
            chart_df[stat].min(),
            color="#FBBF24",
            alpha=0.10
        )

        add_point_labels(ax, chart_df["year"], chart_df[stat], stat)
        add_y_padding(ax, chart_df[stat])

        style_graph(
            fig,
            ax,
            title=pretty_stat_name(stat),
            xlabel="Season",
            ylabel=pretty_stat_name(stat)
        )

        with cols[i % 2]:
            st.markdown('<div class="block-card">', unsafe_allow_html=True)
            st.pyplot(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        plt.close(fig)


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

    if "year" not in df1.columns or "year" not in df2.columns:
        st.warning("Year column missing.")
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

    st.subheader(f"{p1} vs {p2} — {pretty_stat_name(stat)}")

    st.dataframe(merged, use_container_width=True)

    fig, ax = plt.subplots(figsize=(8.4, 4.2))

    ax.plot(
        merged["Year"],
        merged[p1],
        marker="o",
        linewidth=2.6,
        markersize=7,
        label=p1,
        color="#FBBF24",
        markerfacecolor="#FCD34D",
        markeredgecolor="#111827",
        markeredgewidth=1.5
    )

    ax.plot(
        merged["Year"],
        merged[p2],
        marker="o",
        linewidth=2.6,
        markersize=7,
        label=p2,
        color="#38BDF8",
        markerfacecolor="#7DD3FC",
        markeredgecolor="#111827",
        markeredgewidth=1.5
    )

    add_point_labels(ax, merged["Year"], merged[p1], stat)
    add_point_labels(ax, merged["Year"], merged[p2], stat)

    combined_values = pd.concat([merged[p1], merged[p2]], ignore_index=True)
    add_y_padding(ax, combined_values)

    style_graph(
        fig,
        ax,
        title=f"{p1} vs {p2}",
        xlabel="Season",
        ylabel=pretty_stat_name(stat)
    )

    legend = ax.legend(
        facecolor="#0B1020",
        edgecolor="#374151",
        labelcolor="#F9FAFB",
        framealpha=1
    )

    for text in legend.get_texts():
        text.set_color("#F9FAFB")

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


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
