import sqlite3
import matplotlib
import matplotlib.pyplot as plt  # type:  ignore

matplotlib.use("TkAgg")


def search_player_by_name(name):
    # Connect to the SQLite database
    conn = sqlite3.connect('bb_stats.db')
    cursor = conn.cursor()

    # Use LOWER() for case-insensitive search
    cursor.execute("SELECT * FROM players WHERE LOWER(name) = LOWER(?)", (name,))
    players = cursor.fetchall()

    if players:
        print(f"Players found for '{name}':")
        years = []
        batting_averages = []

        for player in players:
            player_id, name, school, ba, era, year = player
            print(f"ID: {player_id}")
            print(f"Name: {name}")
            print(f"School: {school}")
            print(f"Batting Average: {ba}")
            print(f"ERA: {era}")
            print(f"Year: {year}")
            print("-" * 40)

            # Make sure BA and year are valid numbers
            try:
                ba_value = float(ba)
                year_value = int(year)
                batting_averages.append(ba_value)
                years.append(year_value)
            except:  # noqa: E722
                pass  # Skip invalid entries

        # Plotting
        if years and batting_averages:
            plt.figure(figsize=(8, 5))
            plt.plot(years, batting_averages, marker='o', linestyle='-', color='blue')
            plt.title(f"{name} - Batting Average Over Years")
            plt.xlabel("Year")
            plt.ylabel("Batting Average")
            plt.ylim(0, 1)  # Optional: keep Y axis between 0 and 1
            plt.xticks(years)
            plt.grid(True, linestyle='--', linewidth=0.5)
            plt.tight_layout()
            plt.show()
        else:
            print("No valid batting average data available to plot.")
    else:
        print(f"No player found with the name '{name}'.")

    conn.close()


# Main execution
if __name__ == "__main__":
    player_name = input("Enter the player's name: ").strip()
    search_player_by_name(player_name)
