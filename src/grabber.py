import time
import csv
from typing import List, Dict
from bs4 import BeautifulSoup  # type: ignore
from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
from code import csv_to_master_db  # updated loader that creates/uses local DB

# --- Teams to scrape ---
TEAMS = {
    "wj": "Washington & Jefferson",
    "all": "Allegheny",
    "gro": "Grove City",
    "svc": "Saint Vincent",
    "wes": "Westminster",
    "thi": "Thiel",
    "cha": "Chatham",
    "bet": "Bethany",
    "way": "Waynesburg",
    "fra": "Franciscan",
    "gen": "Geneva"
}

# --- Important stats per section ---
IMPORTANT_STATS = {
    "hitting": ["AVG", "AB", "R", "H"],
    "pitching": ["ERA", "W-L", "IP"],
    "fielding": ["FLD%", "C", "E"]  # fielding percentage, total chances, errors
}

# --- Column mapping to DB ---
COLUMN_MAP = {
    "AVG": "ba",
    "AB": "ab",
    "R": "runs",
    "H": "hits",
    "ERA": "era",
    "W-L": "wl",
    "IP": "ip",
    "FLD%": "fld_pct",
    "C": "total_chances",
    "E": "errors"
}


class Player:
    def __init__(self, name: str, team: str, stats: List[str]):
        self.name = name
        self.team = team
        self.stats = stats
        for stat in stats:
            setattr(self, COLUMN_MAP.get(stat, stat), None)
        self.year = None

    def set_stats(self, values: Dict[str, str]):
        for stat, value in values.items():
            mapped = COLUMN_MAP.get(stat, stat)
            setattr(self, mapped, value)

    def as_dict(self):
        data = {
            "name": self.name,
            "school": self.team,
            "year": self.year
        }
        data.update({COLUMN_MAP.get(stat, stat): getattr(self, COLUMN_MAP.get(stat, stat)) for stat in self.stats})
        return data


def extract_players(soup: BeautifulSoup, section_id: str, team: str) -> List[Player]:
    section = soup.find(id=section_id)
    if not section:
        print(f"⚠️ Section '{section_id}' not found.")
        return []

    table = section.find("table")
    if not table:
        print(f"⚠️ No table found in section '{section_id}'.")
        return []

    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
    important = IMPORTANT_STATS[section_id]

    players = []

    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        name = cells[0].get_text(strip=True)
        values = {}

        for header, cell in zip(headers[1:], cells[1:]):
            if header in important:
                values[header] = cell.get_text(strip=True)

        player = Player(name, team, important)
        player.set_stats(values)
        players.append(player)

    return players


def write_csv(players: List[Player], filename: str, year: int):
    if not players:
        print(f"⚠ No data to write for {filename}")
        return

    for p in players:
        p.year = year

    fieldnames = ["name", "school"] + [COLUMN_MAP.get(stat, stat) for stat in players[0].stats] + ["year"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in players:
            writer.writerow(p.as_dict())

    print(f"✅ Wrote {len(players)} players → {filename}")


def scrape_team(team_code: str, team_name: str, year: int = 2025):  # int should be year of current scrape
    print(f"\n🚀 Scraping {team_name} ({year})")

    url = f"https://pacathletics.org/teamstats.aspx?path=baseball&year={year}&school={team_code}"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    for section in ["hitting", "pitching", "fielding"]:
        players = extract_players(soup, section, team_name)
        filename = f"{year}_{team_code}_{section}.csv"

        if players:
            write_csv(players, filename, year)
            csv_to_master_db(filename, section)  # uses local statdb.db
        else:
            print(f"⚠ No data found for {team_name} {section}, skipping DB load.")


def main():
    year = 2025
    for team_code, team_name in TEAMS.items():
        scrape_team(team_code, team_name, year)
        time.sleep(5)


if __name__ == "__main__":
    main()
