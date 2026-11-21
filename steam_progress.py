#!/usr/bin/env python3
"""Publica o estado das conquistas Steam sem divulgar credenciais nem spoilers pendentes."""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

STEAM_ID = "76561199102269125"
APP_ID = 750920
OUT = Path("achievements.json")

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "SteamAchievementsSync/1.0", "Accept": "application/xml, application/json"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()

def public_xml():
    url = f"https://steamcommunity.com/profiles/{STEAM_ID}/stats/{APP_ID}/achievements/?xml=1&l=english"
    root = ET.fromstring(fetch(url))
    if root.tag != "playerstats":
        raise ValueError("Unexpected Steam XML response")
    achievements = []
    for node in root.findall("./achievements/achievement"):
        identifier = (node.findtext("apiname") or "").strip()
        if not identifier:
            continue
        achieved = node.get("closed") == "1"
        stamp = node.findtext("unlockTimestamp")
        achievements.append({"id": identifier, "achieved": achieved,
            "name": node.findtext("name") if achieved else None,
            "unlock_timestamp": int(stamp) if achieved and stamp and stamp.isdigit() else None})
    if not achievements:
        raise ValueError("No achievements with API identifiers in public XML")
    return achievements, "steam-community-xml"

def web_api():
    key = os.environ.get("STEAM_API_KEY", "").strip()
    if not key:
        raise ValueError("The public XML source failed and STEAM_API_KEY is not configured")
    query = urllib.parse.urlencode({"key": key, "steamid": STEAM_ID, "appid": APP_ID, "l": "english"})
    result = json.loads(fetch("https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?" + query))
    stats = result.get("playerstats", {})
    if not stats.get("success") or not stats.get("achievements"):
        raise ValueError("Steam API did not return achievements (check profile privacy and key)")
    return [{"id": a["apiname"], "achieved": bool(a.get("achieved")),
             "name": a.get("name") if a.get("achieved") else None,
             "unlock_timestamp": a.get("unlocktime") or None if a.get("achieved") else None}
            for a in stats["achievements"]], "steam-web-api"

def main():
    try:
        achievements, source = public_xml()
    except Exception as exc:
        print(f"Public XML unavailable ({type(exc).__name__}); trying the official API.")
        try:
            achievements, source = web_api()
        except Exception as api_exc:
            raise SystemExit(str(api_exc)) from None
    ids = [a["id"] for a in achievements]
    if len(ids) != len(set(ids)):
        raise SystemExit("Duplicate achievement identifiers; will not overwrite previous data")
    unlocked = sorted((a for a in achievements if a["achieved"]), key=lambda x: x["id"])
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if set(previous.get("unlocked_ids", [])) - {a["id"] for a in unlocked}:
            raise SystemExit("Steam returned fewer unlocked achievements than before; previous data preserved")
    result = {"game": "Shadow of the Tomb Raider", "steam_id": STEAM_ID, "app_id": APP_ID,
              "updated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "source": source, "total": len(achievements), "unlocked_count": len(unlocked),
              "unlocked_ids": [a["id"] for a in unlocked], "unlocked": unlocked,
              "locked_ids": sorted(a["id"] for a in achievements if not a["achieved"])}
    if OUT.exists() and previous.get("unlocked_ids") == result["unlocked_ids"] and previous.get("total") == result["total"]:
        print("No new achievements; keeping the existing file without creating a commit")
        return
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Synced {len(unlocked)}/{len(achievements)} achievements from {source}")

if __name__ == "__main__":
    main()
