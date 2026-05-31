"""
Fetch MotoGP 2026 standings and schedule from the official MotoGP API.
Saves results to data/standings.json and data/schedule.json.
"""

import json
import sys
import os
from datetime import datetime, timezone

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124",
    "Accept": "application/json",
    "Origin": "https://www.motogp.com",
    "Referer": "https://www.motogp.com/",
}

SEASON_YEAR = 2026

# ── helpers ──────────────────────────────────────────────────────────────────

def get(url, **kwargs):
    r = requests.get(url, headers=HEADERS, timeout=15, **kwargs)
    r.raise_for_status()
    return r.json()


def flag(country_iso):
    """Convert 2-letter ISO to flag emoji."""
    if not country_iso or len(country_iso) != 2:
        return ""
    return chr(0x1F1E0 + ord(country_iso[0].upper()) - 65) + \
           chr(0x1F1E0 + ord(country_iso[1].upper()) - 65)


# ── MotoGP official API (reverse-engineered from motogp.com app) ─────────────

BASE = "https://api.motogp.com/riders-api/2.0"

def fetch_season_uuid():
    seasons = get(f"{BASE}/seasons")
    for s in seasons:
        if s.get("year") == SEASON_YEAR:
            return s["id"]
    return None


def fetch_category_uuid(season_uuid):
    cats = get(f"{BASE}/categories?seasonUuid={season_uuid}")
    for c in cats:
        if c.get("name", "").upper() == "MOTOGP":
            return c["id"]
    return None


def fetch_rider_standings(season_uuid, category_uuid):
    data = get(
        f"{BASE}/standings",
        params={
            "seasonUuid": season_uuid,
            "categoryUuid": category_uuid,
        },
    )
    # The API returns a list of classification objects
    results = []
    entries = data if isinstance(data, list) else data.get("classification", [])
    for entry in entries[:20]:
        rider = entry.get("rider", {})
        country = (rider.get("country") or {}).get("iso", "")
        results.append({
            "pos": entry.get("position", 0),
            "num": str(rider.get("number", "")),
            "name": f"{rider.get('name','')} {rider.get('surname','')}".strip(),
            "team": (entry.get("team") or {}).get("name", ""),
            "pts": entry.get("points", 0),
            "flag": flag(country),
        })
    return results


def fetch_constructor_standings(season_uuid, category_uuid):
    data = get(
        f"{BASE}/constructorStandings",
        params={
            "seasonUuid": season_uuid,
            "categoryUuid": category_uuid,
        },
    )
    results = []
    entries = data if isinstance(data, list) else data.get("classification", [])
    for entry in entries[:10]:
        constructor = entry.get("constructor", {})
        country = (constructor.get("country") or {}).get("iso", "")
        results.append({
            "pos": entry.get("position", 0),
            "name": constructor.get("name", ""),
            "pts": entry.get("points", 0),
            "flag": flag(country),
        })
    return results


def fetch_schedule(season_uuid, category_uuid):
    events = get(f"{BASE}/events", params={"seasonUuid": season_uuid, "isFinished": "false"})
    schedule = []
    now = datetime.now(timezone.utc)
    for ev in events:
        date_str = ev.get("date_start", "") or ev.get("dateStart", "")
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            dt = None
        schedule.append({
            "name": ev.get("name", ""),
            "circuit": (ev.get("circuit") or {}).get("name", ""),
            "country": (ev.get("country") or {}).get("name", ""),
            "flag": flag((ev.get("country") or {}).get("iso", "")),
            "date": date_str[:10] if date_str else "",
            "status": "past" if (dt and dt < now) else "upcoming",
        })
    # sort by date, take next 6 upcoming
    upcoming = sorted(
        [s for s in schedule if s["status"] == "upcoming"],
        key=lambda x: x["date"],
    )
    return upcoming[:6]


# ── fallback data (used if API is unavailable) ────────────────────────────────

FALLBACK_RIDERS = [
    {"pos":1,"num":"93","name":"Marc Márquez","team":"Gresini Ducati","pts":245,"flag":"🇪🇸"},
    {"pos":2,"num":"1","name":"Pecco Bagnaia","team":"Ducati Lenovo","pts":198,"flag":"🇮🇹"},
    {"pos":3,"num":"12","name":"Maverick Viñales","team":"Aprilia Racing","pts":167,"flag":"🇪🇸"},
    {"pos":4,"num":"25","name":"Raul Fernández","team":"Trackhouse Aprilia","pts":142,"flag":"🇪🇸"},
    {"pos":5,"num":"5","name":"Johann Zarco","team":"LCR Honda","pts":119,"flag":"🇫🇷"},
    {"pos":6,"num":"72","name":"Marco Bezzecchi","team":"Trackhouse Aprilia","pts":98,"flag":"🇮🇹"},
    {"pos":7,"num":"33","name":"Brad Binder","team":"Red Bull KTM","pts":87,"flag":"🇿🇦"},
    {"pos":8,"num":"73","name":"Alex Márquez","team":"Gresini Ducati","pts":76,"flag":"🇪🇸"},
    {"pos":9,"num":"41","name":"Aleix Espargaro","team":"Aprilia Racing","pts":62,"flag":"🇪🇸"},
    {"pos":10,"num":"10","name":"Luca Marini","team":"Repsol Honda","pts":55,"flag":"🇮🇹"},
]

FALLBACK_CONSTRUCTORS = [
    {"pos":1,"name":"Ducati","pts":443,"flag":"🇮🇹"},
    {"pos":2,"name":"Aprilia","pts":309,"flag":"🇮🇹"},
    {"pos":3,"name":"Honda","pts":198,"flag":"🇯🇵"},
    {"pos":4,"name":"KTM","pts":145,"flag":"🇦🇹"},
    {"pos":5,"name":"Yamaha","pts":112,"flag":"🇯🇵"},
]

FALLBACK_SCHEDULE = [
    {"name":"German Grand Prix","circuit":"Sachsenring","country":"Germany","flag":"🇩🇪","date":"2026-07-06","status":"upcoming"},
    {"name":"British Grand Prix","circuit":"Silverstone","country":"United Kingdom","flag":"🇬🇧","date":"2026-08-03","status":"upcoming"},
    {"name":"Austrian Grand Prix","circuit":"Red Bull Ring","country":"Austria","flag":"🇦🇹","date":"2026-08-24","status":"upcoming"},
    {"name":"San Marino Grand Prix","circuit":"Misano World Circuit","country":"Italy","flag":"🇮🇹","date":"2026-09-14","status":"upcoming"},
    {"name":"Aragón Grand Prix","circuit":"MotorLand Aragón","country":"Spain","flag":"🇪🇸","date":"2026-09-28","status":"upcoming"},
]


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs("data", exist_ok=True)
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    source = "api"

    riders = []
    constructors = []
    schedule = []

    try:
        print("Fetching season UUID...")
        season_uuid = fetch_season_uuid()
        if not season_uuid:
            raise ValueError(f"Season {SEASON_YEAR} not found in API")

        print(f"Season UUID: {season_uuid}")
        category_uuid = fetch_category_uuid(season_uuid)
        if not category_uuid:
            raise ValueError("MotoGP category not found")

        print(f"Category UUID: {category_uuid}")
        riders = fetch_rider_standings(season_uuid, category_uuid)
        constructors = fetch_constructor_standings(season_uuid, category_uuid)
        schedule = fetch_schedule(season_uuid, category_uuid)
        print(f"Got {len(riders)} riders, {len(constructors)} constructors, {len(schedule)} events")

    except Exception as e:
        print(f"API error: {e} — using fallback data", file=sys.stderr)
        riders = FALLBACK_RIDERS
        constructors = FALLBACK_CONSTRUCTORS
        schedule = FALLBACK_SCHEDULE
        source = "fallback"

    standings_payload = {
        "updatedAt": updated_at,
        "source": source,
        "season": SEASON_YEAR,
        "riders": riders,
        "constructors": constructors,
    }
    schedule_payload = {
        "updatedAt": updated_at,
        "source": source,
        "season": SEASON_YEAR,
        "events": schedule,
    }

    with open("data/standings.json", "w", encoding="utf-8") as f:
        json.dump(standings_payload, f, ensure_ascii=False, indent=2)

    with open("data/schedule.json", "w", encoding="utf-8") as f:
        json.dump(schedule_payload, f, ensure_ascii=False, indent=2)

    print(f"Saved data/standings.json and data/schedule.json  [{source}]")


if __name__ == "__main__":
    main()
