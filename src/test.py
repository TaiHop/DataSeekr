import sqlite3
import random
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

DB_PATH = "statdb.db"

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
    "hir": "Hiram"
}

IMPORTANT_STATS = {
    "hitting": ["AVG", "AB", "R", "H", "RBI"],
    "pitching": ["ERA", "W-L", "IP", "SO", "BB"],
    "fielding": ["FLD%", "C", "E"]
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
    "E": "errors"
}


# ------------------------
# NAME MATCHING (ROBUST)
# ------------------------

def extract_all_name_parts(name):
    name = name.lower().replace(".", "").strip()
    parts = re.split(r"[,\s]+", name)
    parts = [p for p in parts if p]

    if len(parts) < 2:
        return []

    combos = []

    combos.append((parts[0], parts[-1]))     # first last
    combos.append((parts[-1], parts[0]))     # reversed

    if "," in name:
        last, first = name.split(",", 1)
        combos.append((first.strip(), last.strip()))

    return combos


def names_match(db_name, site_name):
    db_combos = extract_all_name_parts(db_name)
    site_combos = extract_all_name_parts(site_name)

    for db_first, db_last in db_combos:
        for site_first, site_last in site_combos:
            if db_last == site_last and db_first[0] == site_first[0]:
                return True

    return False


# ------------------------
# STAT NORMALIZATION
# ------------------------

def normalize_stat(value):
    if value is None:
        return None

    value = str(value).strip()

    if value.startswith("."):
        value = "0" + value

    try:
        return float(value)
    except:
        return value


# ------------------------
# DB
# ------------------------

def get_random_section():
    return random.choice(["hitting", "pitching", "fielding"])


def get_player(team, section):
    conn = sqlite3.connect(DB_PATH)

    table = f"{section}_stats"
    cols = ["name"] + [COLUMN_MAP[s] for s in IMPORTANT_STATS[section]]

    # ✅ FILTER BY YEAR 2026 ADDED HERE
    query = f"""
    SELECT {",".join(cols)}
    FROM {table}
    WHERE school = ?
      AND year = 2026
    ORDER BY RANDOM()
    LIMIT 1
    """

    player = conn.execute(query, (team,)).fetchone()
    conn.close()

    return player


# ------------------------
# SCRAPING
# ------------------------

def scrape(team_code):
    url = f"https://pacathletics.org/teamstats.aspx?path=baseball&year=2026&school={team_code}"

    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    return soup


def get_index_map(table, section):
    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]

    return {
        h: i for i, h in enumerate(headers)
        if h in IMPORTANT_STATS[section]
    }


def find_player(soup, section, db_name):
    section_html = soup.find(id=section)

    if not section_html:
        return None, None, None

    table = section_html.find("table")
    if not table:
        return None, None, None

    index_map = get_index_map(table, section)
    rows = table.find("tbody").find_all("tr")

    for row in rows:
        cells = row.find_all(["th", "td"])

        if not cells:
            continue

        site_name = cells[0].get_text(strip=True)

        if names_match(db_name, site_name):
            return cells, index_map, site_name

    return None, None, None


# ------------------------
# SINGLE TEST RUN
# ------------------------

def run_test(test_num):
    team_code, team_name = random.choice(list(TEAMS.items()))
    section = get_random_section()

    print(f"\n[{test_num}] 🏫 {team_name} | 📂 {section}")

    player = get_player(team_name, section)

    if not player:
        print("⚠ No player found")
        return False

    name = player[0]
    stat_values = player[1:]
    stat_names = IMPORTANT_STATS[section]

    valid = [
        (stat, val)
        for stat, val in zip(stat_names, stat_values)
        if val not in (None, "", 0, 0.0)
    ]

    if not valid:
        print(f"⚠ No valid stats → {name}")
        return False

    stat_to_check, db_val = random.choice(valid)

    print(f"🔎 {name} | {stat_to_check}")

    soup = scrape(team_code)

    cells, index_map, site_name = find_player(soup, section, name)

    if not cells:
        print("❌ Player not found")
        return False

    idx = index_map.get(stat_to_check)

    if idx is None or idx >= len(cells):
        print("⚠ Stat missing on site")
        return False

    site_val = cells[idx].get_text(strip=True)

    if normalize_stat(db_val) == normalize_stat(site_val):
        print(f"✅ PASS ({site_name})")
        return True
    else:
        print(f"❌ FAIL ({site_name}) DB={db_val} SITE={site_val}")
        return False


# ------------------------
# MAIN (20 TESTS)
# ------------------------

def main():
    total = 20
    passed = 0

    for i in range(1, total + 1):
        if run_test(i):
            passed += 1

    print("\n====================")
    print(f"RESULTS: {passed}/{total} PASSED")

    accuracy = (passed / total) * 100
    print(f"ACCURACY: {accuracy:.2f}%")

    if accuracy >= 95:
        print("🔥 EXCELLENT DATA")
    elif accuracy >= 80:
        print("⚠ GOOD BUT NEEDS CLEANUP")
    else:
        print("❌ DATA ISSUES DETECTED")


if __name__ == "__main__":
    main()
