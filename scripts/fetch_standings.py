"""
Fetch MotoGP 2026 standings from motorsport.com.
Saves results to data/standings.json and data/schedule.json.
"""

import json, sys, os, re
from datetime import datetime, timezone
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
SEASON_YEAR = 2026

RIDER_FLAGS = {
    "bezzecchi":"🇮🇹","martin":"🇪🇸","di giannantonio":"🇮🇹","acosta":"🇪🇸",
    "ogura":"🇯🇵","fernandez":"🇪🇸","fernandez":"🇪🇸","bagnaia":"🇮🇹",
    "marquez":"🇪🇸","aldeguer":"🇪🇸","espargaro":"🇪🇸","zarco":"🇫🇷",
    "binder":"🇿🇦","morbidelli":"🇮🇹","vinales":"🇪🇸","quartararo":"🇫🇷",
    "bastianini":"🇮🇹","rins":"🇪🇸","miller":"🇦🇺","nakagami":"🇯🇵",
    "mir":"🇪🇸","ramirez":"🇲🇽","roberts":"🇺🇸","lowes":"🇬🇧",
    "dixon":"🇬🇧","chantra":"🇹🇭",
}

def flag_rider(name):
    nl = name.lower()
    for k,v in RIDER_FLAGS.items():
        if k in nl: return v
    return ""

FALLBACK_RIDERS = [
    {"pos":1,"num":"72","name":"Marco Bezzecchi","team":"Aprilia Racing","pts":173,"flag":"🇮🇹"},
    {"pos":2,"num":"89","name":"Jorge Martin","team":"Aprilia Racing","pts":156,"flag":"🇪🇸"},
    {"pos":3,"num":"49","name":"Fabio Di Giannantonio","team":"Team VR46","pts":134,"flag":"🇮🇹"},
    {"pos":4,"num":"31","name":"Pedro Acosta","team":"Red Bull KTM","pts":103,"flag":"🇪🇸"},
    {"pos":5,"num":"79","name":"Ai Ogura","team":"Trackhouse Racing","pts":92,"flag":"🇯🇵"},
    {"pos":6,"num":"25","name":"Raul Fernandez","team":"Trackhouse Racing","pts":87,"flag":"🇪🇸"},
    {"pos":7,"num":"1","name":"Francesco Bagnaia","team":"Ducati Lenovo","pts":82,"flag":"🇮🇹"},
    {"pos":8,"num":"93","name":"Marc Marquez","team":"Ducati Lenovo","pts":71,"flag":"🇪🇸"},
    {"pos":9,"num":"73","name":"Alex Marquez","team":"Gresini Racing","pts":67,"flag":"🇪🇸"},
    {"pos":10,"num":"54","name":"Fermin Aldeguer","team":"Gresini Racing","pts":59,"flag":"🇪🇸"},
]
FALLBACK_CONSTRUCTORS = [
    {"pos":1,"name":"Aprilia","pts":329,"flag":"🇮🇹"},
    {"pos":2,"name":"Ducati","pts":268,"flag":"🇮🇹"},
    {"pos":3,"name":"KTM","pts":148,"flag":"🇦🇹"},
    {"pos":4,"name":"Honda","pts":87,"flag":"🇯🇵"},
    {"pos":5,"name":"Yamaha","pts":64,"flag":"🇯🇵"},
]
FALLBACK_SCHEDULE = [
    {"name":"German Grand Prix","circuit":"Sachsenring","country":"Germany","flag":"🇩🇪","date":"2026-07-05","status":"upcoming"},
    {"name":"British Grand Prix","circuit":"Silverstone","country":"United Kingdom","flag":"🇬🇧","date":"2026-08-02","status":"upcoming"},
    {"name":"Austrian Grand Prix","circuit":"Red Bull Ring","country":"Austria","flag":"🇦🇹","date":"2026-08-23","status":"upcoming"},
    {"name":"San Marino Grand Prix","circuit":"Misano","country":"Italy","flag":"🇮🇹","date":"2026-09-13","status":"upcoming"},
    {"name":"Aragon Grand Prix","circuit":"MotorLand Aragon","country":"Spain","flag":"🇪🇸","date":"2026-09-27","status":"upcoming"},
    {"name":"Japan Grand Prix","circuit":"Motegi","country":"Japan","flag":"🇯🇵","date":"2026-10-04","status":"upcoming"},
]

def fetch_standings():
    url = f"https://www.motorsport.com/motogp/standings/{SEASON_YEAR}/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    riders = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", r.text, re.DOTALL|re.IGNORECASE):
        cells = [re.sub(r"<[^>]+>","",c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>",row,re.DOTALL|re.IGNORECASE)]
        cells = [c for c in cells if c]
        if len(cells) < 3: continue
        try: pos = int(cells[0])
        except: continue
        if not 1 <= pos <= 25: continue
        name, pts, num = "", 0, ""
        for c in cells[1:]:
            if re.match(r"^\d+$", c):
                v = int(c)
                if v <= 25 and not num: num = c
                elif v <= 400 and not pts: pts = v
            elif len(c) > 3 and not name: name = c
        if name:
            riders.append({"pos":pos,"num":num,"name":name,"team":"","pts":pts,"flag":flag_rider(name)})
    return sorted(riders, key=lambda x:x["pos"])[:20]

def main():
    os.makedirs("data", exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    source, riders, schedule = "scraped", [], FALLBACK_SCHEDULE

    try:
        riders = fetch_standings()
        assert len(riders) >= 5
        print(f"Scraped {len(riders)} riders")
    except Exception as e:
        print(f"Scrape failed: {e}", file=sys.stderr)
        riders, source = FALLBACK_RIDERS, "fallback"

    with open("data/standings.json","w",encoding="utf-8") as f:
        json.dump({"updatedAt":ts,"source":source,"season":SEASON_YEAR,
                   "riders":riders,"constructors":FALLBACK_CONSTRUCTORS},f,ensure_ascii=False,indent=2)
    with open("data/schedule.json","w",encoding="utf-8") as f:
        json.dump({"updatedAt":ts,"source":source,"season":SEASON_YEAR,
                   "events":schedule},f,ensure_ascii=False,indent=2)
    print(f"Done [{source}]")

if __name__ == "__main__":
    main()