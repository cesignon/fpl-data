"""
Snapshot the public FPL API into data/ as JSON.

Run by GitHub Actions on a schedule (see .github/workflows/fetch.yml) or by hand:
    python fetch.py

No login, no secrets — every endpoint here is public.
"""
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://fantasy.premierleague.com/api/"
TEAM_ID = 7344682          # What The Hecke
LEAGUE_ID = 960192         # The Nannery Cup
OUT = Path("data")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

failures = []


def get(path, retries=3):
    """GET a JSON endpoint with a browser-like User-Agent and simple retries."""
    url = BASE + path
    for attempt in range(1, retries + 1):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urlopen(req, timeout=30) as r:
                return json.load(r)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == retries:
                failures.append(f"{path}: {e}")
                return None
            time.sleep(2 * attempt)


def save(rel, obj):
    if obj is None:
        return
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def main():
    OUT.mkdir(exist_ok=True)

    bootstrap = get("bootstrap-static/")
    if bootstrap is None:
        print("bootstrap-static failed — aborting", file=sys.stderr)
        sys.exit(1)
    save("bootstrap-static.json", bootstrap)

    events = bootstrap["events"]
    current = next((e["id"] for e in events if e["is_current"]), None)
    nxt = next((e["id"] for e in events if e["is_next"]), None)

    save("fixtures.json", get("fixtures/"))

    # My team
    save(f"entry/{TEAM_ID}/summary.json", get(f"entry/{TEAM_ID}/"))
    save(f"entry/{TEAM_ID}/history.json", get(f"entry/{TEAM_ID}/history/"))
    my_picks = None
    if current:
        my_picks = get(f"entry/{TEAM_ID}/event/{current}/picks/")
        save(f"entry/{TEAM_ID}/picks-gw{current}.json", my_picks)
        save(f"live/gw{current}.json", get(f"event/{current}/live/"))

    # Per-player detail for my current 15 (per-GW history, past seasons, upcoming fixtures)
    if my_picks:
        for p in my_picks.get("picks", []):
            pid = p["element"]
            save(f"element-summary/{pid}.json", get(f"element-summary/{pid}/"))

    # League table (handles >50 entries)
    standings = []
    page = 1
    league_meta = None
    while True:
        lg = get(f"leagues-classic/{LEAGUE_ID}/standings/?page_standings={page}")
        if lg is None:
            break
        if league_meta is None:
            league_meta = {k: v for k, v in lg.items() if k != "standings"}
        standings.extend(lg["standings"]["results"])
        if not lg["standings"].get("has_next"):
            break
        page += 1
    if league_meta is not None:
        save(f"league/{LEAGUE_ID}.json", {"league": league_meta, "standings": standings})

    # Every league manager's picks + chip history for the current GW (rival watch / league analysis)
    if current and standings:
        picks = {}
        for row in standings:
            eid = row["entry"]
            pk = get(f"entry/{eid}/event/{current}/picks/")
            hist = get(f"entry/{eid}/history/")
            picks[str(eid)] = {
                "player_name": row["player_name"],
                "entry_name": row["entry_name"],
                "rank": row["rank"],
                "total": row["total"],
                "picks": pk,
                "chips": (hist or {}).get("chips"),
                "current": (hist or {}).get("current"),
            }
        save(f"league/picks-gw{current}.json", picks)

    save("meta.json", {
        "fetched_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "current_gw": current,
        "next_gw": nxt,
        "team_id": TEAM_ID,
        "league_id": LEAGUE_ID,
        "failures": failures,
    })

    print(f"done: current GW {current}, next GW {nxt}, {len(failures)} failures")
    for f in failures:
        print("  FAILED", f)


if __name__ == "__main__":
    main()
