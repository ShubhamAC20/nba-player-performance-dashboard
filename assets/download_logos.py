# assets/download_logos.py
# Usage: run from project root (same folder as app.py)
# python assets/download_logos.py

import os
import time
import requests
from bs4 import BeautifulSoup

LOGO_DIR = "assets/logos"
os.makedirs(LOGO_DIR, exist_ok=True)

# Abbrev -> full name map (we used this earlier for mapping)
team_map = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"
}

HEADERS = {"User-Agent": "nba-logo-downloader/1.0 (+https://github.com/yourusername)"}

def download_file(url, path, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200 and r.content:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        # silent fail here, caller will retry/fallback
        pass
    return False

def try_espn(abbrev):
    # ESPN pattern (lowercase abbrev)
    url = f"https://a.espncdn.com/i/teamlogos/nba/500/{abbrev.lower()}.png"
    return url

def try_wikipedia(team_full_name):
    # construct wiki url
    page = team_full_name.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{page}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # look for infobox image
        infobox = soup.find("table", {"class": "infobox"})
        if not infobox:
            imgs = soup.find_all("img")
        else:
            imgs = infobox.find_all("img")
        # prefer svg/png with logo-looking filenames
        for img in imgs:
            src = img.get("src")
            if not src:
                continue
            # normalize src to full url
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = "https://en.wikipedia.org" + src
            # prefer svg or png
            if any(ext in src.lower() for ext in [".svg", ".png"]):
                return src
    except Exception:
        return None
    return None

def main():
    print("Downloading logos into", LOGO_DIR)
    succeeded = []
    failed = []

    for abbr, fullname in team_map.items():
        out_path = os.path.join(LOGO_DIR, f"{abbr}.png")
        # if already exists, skip
        if os.path.exists(out_path):
            print(f"{abbr} exists — skipping.")
            succeeded.append(abbr)
            continue

        print(f"\nAttempting {abbr} ({fullname}) ...")
        # 1) try ESPN
        espn_url = try_espn(abbr)
        ok = download_file(espn_url, out_path)
        if ok:
            print(f"Downloaded from ESPN: {espn_url}")
            succeeded.append(abbr)
            time.sleep(0.3)
            continue

        # 2) try Wikipedia image scrape
        wiki_url = try_wikipedia(fullname)
        if wiki_url:
            ok = download_file(wiki_url, out_path)
            if ok:
                print(f"Downloaded from Wikipedia: {wiki_url}")
                succeeded.append(abbr)
                time.sleep(0.3)
                continue
            else:
                print("Found Wikipedia image but download failed:", wiki_url)

        # 3) fallback: try a secondary pattern (smaller ESPN path)
        alt_url = f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/{abbr.lower()}.png"
        ok = download_file(alt_url, out_path)
        if ok:
            print(f"Downloaded from ESPN alt: {alt_url}")
            succeeded.append(abbr)
            time.sleep(0.3)
            continue

        print(f"Failed to fetch logo for {abbr}. Marking as failed.")
        failed.append(abbr)

    print("\nDone.\nSucceeded:", succeeded)
    if failed:
        print("Failed to download logos for:", failed)
        print("You can download missing logos manually and put them in assets/logos/ as <ABBR>.png")
    else:
        print("All logos downloaded successfully.")

if __name__ == "__main__":
    main()