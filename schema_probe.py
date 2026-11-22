#!/usr/bin/env python3
"""Audita o esquema público de estatísticas do jogo, sem armazenar credenciais."""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

APP_ID = 750920
OUT = Path("schema_probe.json")
TARGETS = {"lastknownposition", "teamkill"}

def main():
    key = os.environ.get("STEAM_API_KEY", "").strip()
    result = {"game": "Shadow of the Tomb Raider", "source": "ISteamUserStats/GetSchemaForGame/v2",
              "status": "unavailable", "stat_identifiers": [],
              "target_achievement_metadata": [], "relevant_stat_identifiers": [],
              "note": "Esquema mostra configuracoes do jogo, nao valores pessoais de progresso."}
    try:
        if not key:
            raise ValueError("missing_api_key")
        q = urllib.parse.urlencode({"key": key, "appid": APP_ID, "l": "english"})
        req = urllib.request.Request(
            "https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?" + q,
            headers={"User-Agent": "SteamAchievementsSchemaProbe/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.load(response)
        schema = data.get("game", {}).get("availableGameStats", {})
        stats = schema.get("stats", [])
        achs = schema.get("achievements", [])
        names = sorted({str(st.get("name", "")) for st in stats if st.get("name")})
        result["stat_identifiers"] = names
        result["numeric_stats_count"] = len(names)
        result["total_achievements_in_schema"] = len(achs)
        result["target_achievement_metadata"] = [
            {"id": a.get("name"), "keys": sorted(a.keys()),
             "progress_related_fields": {k: v for k, v in a.items()
             if "progress" in k.lower() or "stat" in k.lower()}}
            for a in achs if str(a.get("name", "")).lower() in TARGETS
        ]
        relevant_terms = ("lastknown", "teamkill", "last_known", "friendly", "team_kill", "fear")
        result["relevant_stat_identifiers"] = [
            name for name in names if any(term in name.lower() for term in relevant_terms)
        ]
        result["status"] = "ok"
    except Exception as exc:
        # Nunca imprimir ou salvar a URL da requisição (contém a chave).
        result["diagnostic"] = type(exc).__name__
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != output:
        OUT.write_text(output, encoding="utf-8")
    print("Steam schema status: " + result["status"] + ", stats: " + str(len(result["stat_identifiers"])))

if __name__ == "__main__":
    main()
