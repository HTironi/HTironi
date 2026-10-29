import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from html import escape
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "HTironi")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = Path("assets/top-langs.svg")

def github_get(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-languages-card",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def get_repositories():
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{urllib.parse.quote(USERNAME)}/repos"
            f"?type=owner&per_page=100&page={page}"
        )
        batch = github_get(url)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    # Conta apenas repositórios próprios, públicos e não-forks.
    return [r for r in repos if not r.get("fork", False) and not r.get("archived", False)]

def main():
    totals = defaultdict(int)
    for repo in get_repositories():
        languages_url = repo.get("languages_url")
        if not languages_url:
            continue
        try:
            language_data = github_get(languages_url)
        except urllib.error.HTTPError as exc:
            print(f"Aviso: não foi possível ler {repo.get('name')}: HTTP {exc.code}")
            continue
        for language, byte_count in language_data.items():
            totals[language] += int(byte_count)

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:8]
    total_bytes = sum(value for _, value in ranked)

    width, height = 495, max(120, 66 + len(ranked) * 39)
    background = "#0d1117"
    border = "#30363d"
    text_color = "#e6edf3"
    muted = "#8b949e"
    bar_bg = "#21262d"
    palette = ["#f1e05a", "#3572A5", "#e34c26", "#563d7c", "#3178c6",
               "#89e051", "#b07219", "#41b883"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Linguagens mais usadas no GitHub de {escape(USERNAME)}">',
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="8" fill="{background}" stroke="{border}"/>',
        f'<text x="20" y="29" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="600" fill="{text_color}">Linguagens mais usadas</text>',
    ]

    if not ranked or total_bytes == 0:
        parts.append(f'<text x="20" y="65" font-family="Arial, Helvetica, sans-serif" font-size="13" fill="{muted}">Nenhuma linguagem encontrada nos repositórios públicos.</text>')
    else:
        y = 51
        for index, (language, value) in enumerate(ranked):
            percentage = value / total_bytes * 100
            color = palette[index % len(palette)]
            parts.append(f'<text x="20" y="{y+11}" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{text_color}">{escape(language)}</text>')
            parts.append(f'<text x="{width-20}" y="{y+11}" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{muted}">{percentage:.1f}%</text>')
            parts.append(f'<rect x="20" y="{y+18}" width="{width-40}" height="7" rx="3.5" fill="{bar_bg}"/>')
            bar_width = (width - 40) * percentage / 100
            parts.append(f'<rect x="20" y="{y+18}" width="{bar_width:.2f}" height="7" rx="3.5" fill="{color}"/>')
            y += 39

    parts.append("</svg>")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Card criado em {OUTPUT}")

if __name__ == "__main__":
    main()
