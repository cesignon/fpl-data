# fpl-data

Scheduled snapshot of the public Fantasy Premier League API, used by the `fpl-weekly-brief` skill.

- `fetch.py` pulls the endpoints and writes them under `data/`.
- `.github/workflows/fetch.yml` runs it every 6 hours and commits any changes. Use **Actions → Snapshot FPL API → Run workflow** to refresh on demand (e.g. deadline morning).
- `data/meta.json` records when the snapshot was taken, the current/next gameweek, and any endpoints that failed.

Everything here is public API data — no login, no secrets.

## Layout

```
data/
  meta.json
  bootstrap-static.json          players, teams, gameweeks, chips
  fixtures.json                  all fixtures with FDR
  live/gw{N}.json                live points for the current GW
  entry/7344682/                 my team: summary, history, picks-gw{N}
  element-summary/{player}.json  per-GW history for my current 15
  league/960192.json             league table
  league/picks-gw{N}.json        every manager's picks + chips for the current GW
```
