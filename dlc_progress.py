#!/usr/bin/env python3
"""Acompanha as 36 conquistas de DLC sem inferir progresso narrativo."""
import json
from pathlib import Path

SOURCE = Path("achievements.json")
DEST = Path("dlc_progress.json")

# Nomes internos oficiais das conquistas (Steam, app 750920).
DLC = [
    ("The Forge", {
        "tomb": "destinystrialed", "mission": "heirborn",
        "equipment": "bleedingedge", "time_attack": "echoesofthefast",
        "score_attack": "echoesofthefurious"
    }),
    ("The Pillar", {
        "tomb": "thatwasabreeze", "mission": "gowiththeflow",
        "equipment": "eyesofthestorm", "time_attack": "floatlikeabutterfly",
        "score_attack": "stinglikeabee"
    }),
    ("The Nightmare", {
        "tomb": "monkeydo", "mission": "harmony",
        "equipment": "creaturecomforts", "time_attack": "howllong",
        "score_attack": "organgrinder"
    }),
    ("The Price of Survival", {
        "tomb": "mushroomwithaview", "mission": "heaintheavy",
        "equipment": "dressedforsuccess", "time_attack": "gocart",
        "score_attack": "cannonized"
    }),
    ("The Serpent's Heart", {
        "tomb": "hydropower", "mission": "wholeworldblind",
        "equipment": "spoiledforchoice", "time_attack": "rapids",
        "score_attack": "gofish"
    }),
    ("The Grand Caiman", {
        "tomb": "caimanconquered", "mission": "leapinglizards",
        "equipment": "readytorumble", "time_attack": "zipit",
        "score_attack": "offshorecount"
    }),
    ("The Path Home", {
        "tomb": "putherselftogether", "mission": "moonlightsonata",
        "equipment": "moonlitknight", "time_attack": "chelgame",
        "score_attack": "chelattack"
    }),
]
META_ID = "alldlcmissionscomplete"

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    unlocked = set(data["unlocked_ids"])
    groups = []
    total_unlocked = 0
    for label, ids in DLC:
        done = {kind: achievement in unlocked for kind, achievement in ids.items()}
        count = sum(done.values())
        total_unlocked += count
        tips = []
        if done["mission"] and not done["equipment"]:
            tips.append("Missão feita: equipar a combinação de arma e traje da DLC no acampamento.")
        if done["tomb"] and not done["time_attack"]:
            tips.append("Tumba feita: falta bronze no Time Attack da tumba.")
        if done["tomb"] and not done["score_attack"]:
            tips.append("Tumba feita: falta bronze no Score Attack da tumba.")
        groups.append({
            "dlc": label,
            "unlocked": count,
            "total": 5,
            "status_by_kind": done,
            "achievement_ids": ids,
            "next_steps": tips,
        })
    meta_done = META_ID in unlocked
    total_unlocked += int(meta_done)
    result = {
        "source_last_achievement_change_utc": data.get("updated_at_utc"),
        "achievements_total": 36,
        "achievements_unlocked": total_unlocked,
        "achievements_remaining": 36 - total_unlocked,
        "dlc_groups": groups,
        "all_seven_missions_achievement": {
            "id": META_ID, "unlocked": meta_done
        },
        "important": "Estado da Steam; conquista bloqueada nao prova que seja perdivel. Tumbas DLC permitem Time/Score Attack posteriormente."
    }
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if DEST.exists() and DEST.read_text(encoding="utf-8") == output:
        print("Sem mudanca nas conquistas de DLC.")
        return
    DEST.write_text(output, encoding="utf-8")
    print(f"Conquistas DLC: {total_unlocked}/36. Pendentes: {36-total_unlocked}.")

if __name__ == "__main__":
    main()
