# fetch_top_scorers_safe.py
import requests
import pandas as pd
import time
from requests.exceptions import RequestException
from json import JSONDecodeError

BASE = "https://www.balldontlie.io/api/v1"
HEADERS = {"User-Agent": "nba-dashboard/1.0 (+https://github.com/yourusername)"}

def safe_get(url, params=None, attempts=3, backoff=1):
    for i in range(attempts):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        except RequestException as e:
            print(f"Request error (attempt {i+1}/{attempts}):", e)
            time.sleep(backoff)
            continue

        if resp.status_code != 200:
            print(f"Bad status ({resp.status_code}) for {resp.url}")
            print("Response text (first 300 chars):", resp.text[:300])
            time.sleep(backoff)
            continue

        # Some endpoints sometimes return empty body -> error when calling .json()
        if not resp.text or resp.text.strip() == "":
            print(f"Empty response (attempt {i+1}/{attempts}) for {resp.url}")
            time.sleep(backoff)
            continue

        try:
            return resp.json()
        except JSONDecodeError:
            print(f"JSON decode error (attempt {i+1}/{attempts}). Response head:")
            print(resp.text[:500])
            time.sleep(backoff)
            continue

    # all attempts failed
    return None

def fetch_stats(season=2023, per_page=100, max_pages=50):
    page = 1
    rows = []
    while True:
        if page > max_pages:
            print(f"Reached page limit: {max_pages}. Stopping to avoid very long runs.")
            break

        params = {"seasons[]": season, "per_page": per_page, "page": page}
        data = safe_get(f"{BASE}/stats", params=params, attempts=4, backoff=1.5)
        if not data:
            print("Failed to fetch data from API. Stopping.")
            break

        # sanity check
        if "data" not in data or not isinstance(data["data"], list):
            print("Unexpected response structure:", data)
            break

        if len(data["data"]) == 0:
            print("No more data on page", page)
            break

        for item in data["data"]:
            rows.append({
                "player_id": item["player"]["id"],
                "player_name": f"{item['player']['first_name']} {item['player']['last_name']}",
                "team": item["team"]["full_name"],
                "pts": item["pts"],
                "reb": item["reb"],
                "ast": item["ast"],
                "min": item["min"],
                "game_id": item["game"]["id"],
                "date": item["game"]["date"]
            })

        print(f"Fetched page {page} (rows so far: {len(rows)})")
        # pagination meta may be absent sometimes; guard for it
        if data.get("meta") and data["meta"].get("next_page") is None:
            break

        page += 1
        time.sleep(0.5)

    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = fetch_stats(season=2023, per_page=100, max_pages=30)
    if df.empty:
        print("No rows fetched. Exiting.")
    else:
        agg = df.groupby("player_name").agg({"pts":"mean","reb":"mean","ast":"mean"}).reset_index()
        top = agg.sort_values("pts", ascending=False).head(10)
        print(top)
        top.to_csv("top_scorers_2023.csv", index=False)
        print("Saved top_scorers_2023.csv")
