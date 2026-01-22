import sqlite3
import streamlit as st  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import ticker  # type: ignore

st.set_page_config(page_title="Dataseekr Player Search", page_icon="⚾")

st.title("⚾ Dataseekr Player Search")

DB_PATH = "bb_stats.db"

st.write("Database file:", DB_PATH)


def search_player_by_name(name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, school, ba, era, year
        FROM players
        WHERE LOWER(name) LIKE LOWER(?)
        ORDER BY year
        """,
        (f"%{name}%",)
    )

    rows = cursor.fetchall()
    conn.close()

    st.write("Rows returned:", len(rows))  # 🔍 DEBUG

    if not rows:
        st.warning("No matching players found.")
        return

    years, bas = [], []

    for r in rows:
        _, name, school, ba, era, year = r
        st.subheader(f"{name} ({year})")
        st.write(f"School: {school}")
        st.write(f"BA: {ba} | ERA: {era}")
        st.divider()

        try:
            years.append(int(year))
            bas.append(float(ba))
        except:
            pass

    if years and bas:
        fig, ax = plt.subplots()
        ax.plot(years, bas, marker="o")
        ax.set_xlabel("Year")
        ax.set_ylabel("Batting Average")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=5))
        ax.grid(True, linestyle="--", alpha=0.6)
        st.pyplot(fig)  # Display the figure in Streamlit


query = st.text_input("Enter player name")

if query:
    search_player_by_name(query)
