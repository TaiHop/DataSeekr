import csv
import time
from typing import List, Dict

from bs4 import BeautifulSoup  # type: ignore
from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore

from code import csv_to_master_db


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
    "gen": "Geneva",
    "hir": "Hiram",
}

IMPORTANT_STATS = {
    "hitting": ["AVG", "AB", "R", "H", "RBI"],
    "pitching": ["ERA", "W-L", "IP", "SO", "BB"],
    "fielding": ["FLD%", "C", "E"],
}

COLUMN_MAP = {
    "AVG": "ba",
    "AB": "ab",
    "R": "runs",
    "H": "hits",
    "RBI": "rbi",
    "ERA": "era",
    "W-L": "wl",
    "IP": "ip",
    "SO": "so",
    "BB": "bb",
    "FLD%": "fld_pct",
    "C": "total_chances",
    "E": "errors",
}


class Player:
    def __init__(self, name: str, team: str, stats: List[str]):
        self.name = name
        self.team = team
        self.stats = stats
        self.year = None

        for stat in stats:
            setattr(self, COLUMN_MAP.get(stat, stat), None)

    def set_stats(self, values: Dict[str, str]):
        for stat, value in values.items():
            mapped = COLUMN_MAP.get(stat, stat)
            setattr(self, mapped, value)

    def as_dict(self):
        data = {
            "name": self.name,
            "school": self.team,
            "year": self.year,
        }

        for stat in self.stats:
            mapped = COLUMN_MAP.get(stat, stat)
            data[mapped] = getattr(self, mapped)

        return data


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def extract_players(soup: BeautifulSoup, section_id: str, team: str) -> List[Player]:
    section = soup.find(id=section_id)
    if not section:
        print(f"⚠️ Section '{section_id}' not found.")
        return []

    table = section.find("table")
    if not table:
        print(f"⚠️ No table found in section '{section_id}'.")
        return []

    thead = table.find("thead")
    tbody = table.find("tbody")

    if not thead or not tbody:
        print(f"⚠️ Missing table head/body in section '{section_id}'.")
        return []

    headers = [th.get_text(strip=True) for th in thead.find_all("th")]
    important = set(IMPORTANT_STATS[section_id])

    players = []

    for row in tbody.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        name = cells[0].get_text(strip=True)
        if not name:
            continue

        values = {}

        for header, cell in zip(headers[1:], cells[1:]):
            if header in important:
                values[header] = cell.get_text(strip=True)

        player = Player(name, team, IMPORTANT_STATS[section_id])
        player.set_stats(values)
        players.append(player)

    return players


def write_csv(players: List[Player], filename: str, year: int):
    if not players:
        print(f"⚠ No data to write for {filename}")
        return

    for player in players:
        player.year = year

    fieldnames = (
        ["name", "school"]
        + [COLUMN_MAP.get(stat, stat) for stat in players[0].stats]
        + ["year"]
    )

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(player.as_dict() for player in players)

    print(f"✅ Wrote {len(players)} players → {filename}")


def scrape_team(driver, team_code: str, team_name: str, year: int = 2026):
    print(f"\n🚀 Scraping {team_name} ({year})")

    url = (
        f"https://pacathletics.org/teamstats.aspx?"
        f"path=baseball&year={year}&school={team_code}"
    )

    driver.get(url)

    try:
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
    except Exception:
        print(f"⚠ Timed out waiting for tables for {team_name}")
        return

    soup = BeautifulSoup(driver.page_source, "html.parser")

    for section in ["hitting", "pitching", "fielding"]:
        players = extract_players(soup, section, team_name)
        filename = f"{year}_{team_code}_{section}.csv"

        if players:
            write_csv(players, filename, year)
            csv_to_master_db(filename, section)
        else:
            print(f"⚠ No data found for {team_name} {section}, skipping DB load.")


def main():
    year = 2026
    driver = create_driver()

    try:
        for team_code, team_name in TEAMS.items():
            try:
                scrape_team(driver, team_code, team_name, year)
            except Exception as error:
                print(f"❌ Failed scraping {team_name}: {error}")

            time.sleep(1)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
