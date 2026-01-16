import sqlite3
import matplotlib.pyplot as plt  # type: ignore
import streamlit as st           # type: ignore

# --- adapted search function ---


def search_player_by_name(name: str):
    conn = sqlite3.connect('bb_stats.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM players WHERE LOWER(name) = LOWER(?)", (name,))
    players = cursor.fetchall()
    conn.close()

    if not players:
        st.warning(f"No player found with the name '{name}'.")
        return

    years = []
    batting_averages = []

    for player in players:
        player_id, pname, school, ba, era, year = player

        # Display player info
        st.subheader(f"Player: {pname}")
        st.write(f"**ID:** {player_id}")
        st.write(f"**School:** {school}")
        st.write(f"**Batting Average:** {ba}")
        st.write(f"**ERA:** {era}")
        st.write(f"**Year:** {year}")
        st.markdown("---")

        # Collect data for plotting
        try:
            ba_value = float(ba)
            year_value = int(year)
            batting_averages.append(ba_value)
            years.append(year_value)
        except ValueError:
            pass  # Skip invalid entries

    # Plot if data exists
    if years and batting_averages:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(years, batting_averages, marker='o', linestyle='-', color='blue')
        ax.set_title(f"{name} - Batting Average Over Years")
        ax.set_xlabel("Year")
        ax.set_ylabel("Batting Average")
        ax.set_ylim(0, 1)
        ax.set_xticks(years)
        ax.grid(True, linestyle='--', linewidth=0.5)
        st.pyplot(fig)
    else:
        st.info("No valid batting average data available to plot.")

# --- Streamlit UI ---
st.set_page_config(page_title="Baseball Player Search", page_icon="⚾", layout="centered")
st.title("⚾ Baseball Player Search")

query = st.text_input("Enter the player's name:")

if query.strip():
    search_player_by_name(query.strip())
