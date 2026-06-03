"""
Fetch social media follower counts monthly.
Updates data/social.json.

Requirements:
  - YOUTUBE_API_KEY in GitHub Secrets (free from Google Cloud Console)

YouTube API setup (free):
  1. Go to console.cloud.google.com
  2. Create project → Enable "YouTube Data API v3"
  3. Create API Key → add to GitHub repo Settings > Secrets > YOUTUBE_API_KEY
"""

import json
import os
import sys
from datetime import datetime, timezone
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/124"}

# ── Current known counts (fallback if API fails) ──────────────────────────────
KNOWN = {
    "youtube":   {"subscribers": 115000, "display": "115K"},
    "instagram": {"followers":    47700, "display": "47.7K"},
    "facebook":  {"followers":   130000, "display": "130K"},
    "tiktok":    {"followers":   125200, "display": "125K"},
}

CHANNELS = {
    "youtube":   {"url": "https://www.youtube.com/@Lifeofbike_",         "handle": "@Lifeofbike_"},
    "instagram": {"url": "https://www.instagram.com/lifeofbike_",        "handle": "@lifeofbike_"},
    "facebook":  {"url": "https://www.facebook.com/lifeofbikepage/",     "handle": "lifeofbikepage"},
    "tiktok":    {"url": "https://www.tiktok.com/@lifeofbike_",          "handle": "@lifeofbike_"},
}


def fmt(n):
    """Format number: 115000 → '115K', 47700 → '47.7K', 1200000 → '1.2M'"""
    if n >= 1_000_000:
        v = n / 1_000_000
        return f"{v:.1f}M".rstrip("0").rstrip(".")+"M" if "." in f"{v:.1f}" else f"{int(v)}M"
    if n >= 1000:
        v = n / 1000
        s = f"{v:.1f}"
        return s.rstrip("0").rstrip(".") + "K"
    return str(n)


def fetch_youtube(api_key):
    """Fetch YouTube subscriber count via YouTube Data API v3."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics",
        "forHandle": "Lifeofbike_",
        "key": api_key,
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    if not items:
        raise ValueError("No channel found for @Lifeofbike_")
    subs = int(items[0]["statistics"]["subscriberCount"])
    return {"subscribers": subs, "display": fmt(subs)}


def main():
    os.makedirs("data", exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    api_key = os.environ.get("YOUTUBE_API_KEY", "")

    channels_out = {}
    source_map = {}

    # ── YouTube (API) ──────────────────────────────────────────────────────────
    if api_key:
        try:
            yt = fetch_youtube(api_key)
            channels_out["youtube"] = {**CHANNELS["youtube"], **yt}
            source_map["youtube"] = "api"
            print(f"YouTube: {yt['display']} subs  [API]")
        except Exception as e:
            print(f"YouTube API error: {e} — using fallback", file=sys.stderr)
            channels_out["youtube"] = {**CHANNELS["youtube"], **KNOWN["youtube"]}
            source_map["youtube"] = "fallback"
    else:
        print("YOUTUBE_API_KEY not set — using fallback", file=sys.stderr)
        channels_out["youtube"] = {**CHANNELS["youtube"], **KNOWN["youtube"]}
        source_map["youtube"] = "fallback"

    # ── Other platforms (fallback — update KNOWN manually each month) ──────────
    for platform in ["instagram", "facebook", "tiktok"]:
        channels_out[platform] = {**CHANNELS[platform], **KNOWN[platform]}
        source_map[platform] = "manual"
        print(f"{platform.capitalize()}: {KNOWN[platform]['display']}  [manual]")

    payload = {
        "updatedAt": ts,
        "source": source_map,
        "channels": channels_out,
    }

    with open("data/social.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\nSaved data/social.json  [{ts}]")


if __name__ == "__main__":
    main()
