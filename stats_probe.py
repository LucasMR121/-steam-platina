#!/usr/bin/env python3
"""Testa contadores Steam sem expor credenciais ou estatísticas não relacionadas."""
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

STEAM_ID = '76561199102269125'
APP_ID = 750920
OUT = Path('stats_probe.json')
PATTERN = re.compile(r'kill|headshot|head_shot|stealth|melee|focus|perception|endurance|serpent|chain|bow|eagle|takedown|finisher|assassin|fear|enemy|enemies|finish|combo|marksman|supriseairattack|turntables|likeashadow|sixthsense', re.I)

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'SteamAchievementStatsProbe/1.0'})
    with urllib.request.urlopen(req, timeout=22) as resp:
        return resp.read()

def public_statsfeed():
    url = f'https://steamcommunity.com/profiles/{STEAM_ID}/statsfeed/{APP_ID}/?xml=1&schema=1'
    root = ET.fromstring(get(url))
    raw = []
    for node in root.iter():
        if node.tag.rsplit('}', 1)[-1].lower() not in ('stat', 'statinfo'):
            continue
        name = node.get('name') or node.get('id') or node.findtext('name') or node.findtext('id')
        value = node.get('value') or node.findtext('value')
        if name and value is not None:
            raw.append({'name': name, 'value': value})
    if not raw:
        raise ValueError('No raw numeric stats published')
    return raw, 'steam-community-statsfeed'

def web_api():
    key = os.environ.get('STEAM_API_KEY', '').strip()
    if not key:
        raise RuntimeError('STEAM_API_KEY not configured')
    query = urllib.parse.urlencode({'key': key, 'steamid': STEAM_ID, 'appid': APP_ID})
    response = json.loads(get('https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/?' + query))
    stats = response.get('playerstats', {}).get('stats', [])
    if not stats:
        raise ValueError('Steam returned no numeric stats for this title')
    return stats, 'steam-web-api'

def main():
    key_present = bool(os.environ.get('STEAM_API_KEY', '').strip())
    report = {
        'game': 'Shadow of the Tomb Raider',
        'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'steam_api_key_configured': key_present,
        'status': 'stats_unavailable',
        'source': None,
        'numeric_stats_count': 0,
        'possible_combat_counters': [],
        'notice': 'Counter names are not validated against achievement requirements; do not infer exact kills remaining.',
    }
    errors = []
    raw = None
    for name, fn in [('public_statsfeed', public_statsfeed), ('web_api', web_api)]:
        if name == 'web_api' and not key_present:
            errors.append('Steam Web API: key not configured')
            continue
        try:
            raw, report['source'] = fn()
            break
        except Exception as exc:
            # Nunca registrar detalhes de exceções: podem conter a URL com a chave.
            errors.append(f'{name}: {type(exc).__name__}')
    if raw:
        report['status'] = 'stats_found'
        report['numeric_stats_count'] = len(raw)
        report['stat_identifiers'] = sorted(str(item.get('name', ''))[:100] for item in raw)
        for item in raw:
            name = str(item.get('name', ''))
            value = item.get('value')
            if PATTERN.search(name) and isinstance(value, (int, float, str)):
                try:
                    numeric = float(value)
                    if numeric.is_integer():
                        numeric = int(numeric)
                except (ValueError, OverflowError):
                    continue
                report['possible_combat_counters'].append({'name': name[:150], 'value': numeric})
        report['possible_combat_counters'].sort(key=lambda d: d['name'])
        # Só contabilizar conquistas cujo contador Steam foi identificado.
        targets = [
            ('Marksman', 'Marksman_stat', 20),
            ('Surprise!', 'SupriseAirAttack_stat', 5),
            ('Tables Turned', 'TurnTables_stat', 5),
            ('Like a Shadow', 'LikeAShadow_stat', 25),
            ('Sixth Sense', 'SixthSense_stat', 10),
            ('In the Moment', 'InTheMoment_stat', 10),
            ('Made to Endure', 'MadeToEndure_stat', 10),
        ]
        stats_by_name = {str(item.get('name')): item.get('value') for item in raw}
        report['combat_progress'] = []
        for label, stat_name, goal in targets:
            if stat_name not in stats_by_name:
                continue
            try:
                current = max(0, int(stats_by_name[stat_name]))
            except (TypeError, ValueError, OverflowError):
                continue
            report['combat_progress'].append({
                'achievement': label, 'stat_name': stat_name,
                'current': current, 'target': goal,
                'remaining': max(0, goal - current),
                'reached_target': current >= goal
            })
    report['diagnostics'] = errors
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            previous.pop('checked_at_utc', None)
            comparable = dict(report)
            comparable.pop('checked_at_utc', None)
            if previous == comparable:
                print('No changes in available Steam stats')
                return
        except (ValueError, OSError):
            pass
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Stats probe: ' + report['status'] + '; source=' + str(report['source']) + '; raw stat count=' + str(report['numeric_stats_count']))

if __name__ == '__main__':
    main()
