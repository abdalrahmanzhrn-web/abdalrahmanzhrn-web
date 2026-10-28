"""Aggregate GitHub repository statistics across all owned repositories visible to the token."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

LOGIN = 'abdalrahmanzhrn-web'
ROOT = Path(__file__).resolve().parents[1]

def api(path):
    headers = {'User-Agent': LOGIN + '-profile', 'Accept': 'application/vnd.github+json'}
    if os.environ.get('PROFILE_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['PROFILE_TOKEN']
    with urlopen(Request('https://api.github.com' + path, headers=headers), timeout=30) as response:
        return json.load(response)

def main():
    repos = []
    page = 1
    while True:
        path = '/user/repos?affiliation=owner' if os.environ.get('PROFILE_TOKEN') else f'/users/{LOGIN}/repos?type=owner'
        batch = api(path + f'&per_page=100&page={page}')
        repos.extend(r for r in batch if r['owner']['login'].lower() == LOGIN.lower())
        if len(batch) < 100:
            break
        page += 1
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="175" viewBox="0 0 1000 175" role="img" aria-label="Repository statistics"><rect x="1" y="1" width="998" height="173" rx="16" fill="#0d0a08" stroke="#392c24"/><g font-family="Segoe UI,Arial,sans-serif" fill="#eee4d2"><text x="32" y="32" fill="#c19b79" font-size="12" letter-spacing="2">REPOSITORY STATISTICS</text>']
    for i,(value,label) in enumerate([(len(repos),'REPOSITORIES'),(sum(r['stargazers_count'] for r in repos),'STARS'),(sum(r['forks_count'] for r in repos),'FORKS')]):
        y=83
        x=32+i*322
        parts.append(f'<text x="{x}" y="{y}" font-size="28">{value}</text><text x="{x}" y="{y+20}" fill="#ab9983" font-size="10" letter-spacing="1">{label}</text>')
    scope = 'Token-accessible owned repositories' if os.environ.get('PROFILE_TOKEN') else 'Public owned repositories'
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    parts.append(f'<text x="32" y="150" fill="#ab9983" font-size="11">{scope} · {now}</text></g></svg>')
    (ROOT/'assets/stack.svg').write_text('\n'.join(parts),encoding='utf-8')
    print(f'Aggregated {len(repos)} repositories.')

if __name__ == '__main__':
    main()
