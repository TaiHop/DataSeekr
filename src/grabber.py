import time
import csv
from typing import List
from src.code import csv_to_db
from bs4 import BeautifulSoup  # type: ignore
from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore


class Player:
    def __init__(self, name: str = "", stats: List[str] = None):
        self.name = name
        self.stats = stats or []
        for stat in self.stats:
            setattr(self, stat, None)

    def set_stats(self, values: List[str] = None) -> None:
        if not values:
            return
        for stat, value in zip(self.stats, values):
            setattr(self, stat, value)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            **{stat: getattr(self, stat) for stat in self.stats}
        }


def extract_players(soup: BeautifulSoup, section_id: str) -> List[Player]:
    """Extract players from a stats table section identified by `section_id`."""
    section = soup.find(id=section_id)
    if not section:
        print(f"⚠️ Section with ID '{section_id}' not found.")
        return []

    table = section.find("table")
    if not table:
        print(f"⚠️ No table found in section '{section_id}'.")
        return []

    # Extract headers
    header_cells = table.find("thead").find("tr").find_all("th")
    headers = [cell.get_text(strip=True) for cell in header_cells]
    stat_headers = [h for h in headers if h.lower() not in {"#", "index", "player", "name"}]

    # Extract rows
    players = []
    for row in table.find("tbody").find_all("tr", {"role": "row"}):
        cells = row.find_all(["th", "td"])
        if not cells or len(cells) < 2:
            continue

        name = cells[0].get_text(strip=True)
        stat_values = [td.get_text(strip=True) for td in cells[1:len(stat_headers)+1]]
        player = Player(name, stat_headers)
        player.set_stats(stat_values)
        players.append(player)

    return players


def write_csv(players: List[Player], filename: str) -> None:
    if not players:
        print(f"⚠️ No players to write to '{filename}'")
        return

    fieldnames = ["name"] + players[0].stats
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for player in players:
            writer.writerow(player.as_dict())

    print(f"✅ Saved {len(players)} players to '{filename}'")


def scrape_and_save(section_id: str, filename: str, soup: BeautifulSoup) -> None:
    players = extract_players(soup, section_id)
    write_csv(players, filename)


def main():
    url = "https://pacathletics.org/stats.aspx?path=baseball&year=2025"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    sections = {
        "ind_hitting": "2025hitting_stats.csv",
        "ind_pitching": "2025pitching_stats.csv"
    }

    for section_id, filename in sections.items():
        scrape_and_save(section_id, filename, soup)

        if "hitting" in filename:
            table_name = "hitting_stats"
        elif "pitching" in filename:
            table_name = "pitching_stats"
        else:
            table_name = "stats"

        csv_to_db(filename, table_name)


if __name__ == "__main__":
    main()
