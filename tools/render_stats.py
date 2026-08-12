"""Renders the GitHub stats and top-language cards straight from GitHub's GraphQL API.

No third-party card service involved, so there is nothing that can 503.
Output matches the hero: flat, transparent, Primer colours.

Run: GITHUB_TOKEN=... python3 tools/render_stats.py <login> <out_dir>
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com/graphql"

PRIMER = {
    "dark": {
        "fg": "#e6edf3", "muted": "#8b949e", "border": "#30363d",
        "track": "#21262d", "accent": "#2f81f7",
    },
    "light": {
        "fg": "#1f2328", "muted": "#59636e", "border": "#d1d9e0",
        "track": "#eaeef2", "accent": "#0969da",
    },
}

MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

SKIP_LANGS = {"HTML", "CSS", "SCSS", "Less"}


def gql(query, variables, token):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-builder",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


PROFILE_Q = """
query($login: String!, $after: String) {
  user(login: $login) {
    name
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) {
      totalCount
    }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def collect(login, token):
    stars, langs = 0, {}
    after, base = None, None

    while True:
        data = gql(PROFILE_Q, {"login": login, "after": after}, token)["user"]
        base = base or data
        repos = data["repositories"]
        for repo in repos["nodes"]:
            stars += repo["stargazerCount"]
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                if name in SKIP_LANGS:
                    continue
                entry = langs.setdefault(name, {"size": 0, "color": edge["node"]["color"]})
                entry["size"] += edge["size"]
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]

    start = int(base["createdAt"][:4])
    now = datetime.now(timezone.utc).year
    years = range(start, now + 1)
    fields = " ".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z")'
        f" {{ totalCommitContributions restrictedContributionsCount }}"
        for y in years
    )
    contrib = gql(f"query($login: String!) {{ user(login: $login) {{ {fields} }} }}",
                  {"login": login}, token)["user"]
    commits = sum(
        c["totalCommitContributions"] + c["restrictedContributionsCount"]
        for c in contrib.values()
    )

    return {
        "name": base["name"] or login,
        "stars": stars,
        "commits": commits,
        "prs": base["pullRequests"]["totalCount"],
        "issues": base["issues"]["totalCount"],
        "contributed": base["repositoriesContributedTo"]["totalCount"],
        "followers": base["followers"]["totalCount"],
        "langs": langs,
    }


def group(n):
    return f"{n:,}"


def stats_card(d, P):
    rows = [
        ("Total Stars Earned", d["stars"]),
        ("Total Commits", d["commits"]),
        ("Total Pull Requests", d["prs"]),
        ("Total Issues", d["issues"]),
        ("Contributed To", d["contributed"]),
        ("Followers", d["followers"]),
    ]
    W, H = 470, 200
    body = ""
    for i, (label, value) in enumerate(rows):
        y = 74 + i * 21
        body += (
            f'<g opacity="1"><text x="25" y="{y}" font-family="{MONO}" font-size="12" '
            f'fill="{P["muted"]}">{label}</text>'
            f'<text x="{W - 25}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12" '
            f'font-weight="700" fill="{P["fg"]}">{group(value)}</text>'
            f'<animate attributeName="opacity" values="0;1" dur="0.5s" '
            f'begin="{0.15 + i * 0.08:.2f}s" fill="freeze"/></g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" aria-label="GitHub stats">
  <title>{d['name']} — GitHub stats</title>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" ry="6" fill="none" stroke="{P['border']}"/>
  <text x="25" y="40" font-family="{SANS}" font-size="16" font-weight="600" fill="{P['accent']}">{d['name']}&#8217;s GitHub Stats</text>
  <rect x="25" y="50" width="{W - 50}" height="1" fill="{P['border']}">
    <animate attributeName="width" values="0;{W - 50}" dur="0.6s" fill="freeze"/>
  </rect>
  {body}
</svg>
"""


def langs_card(d, P, top=6):
    ranked = sorted(d["langs"].items(), key=lambda kv: kv[1]["size"], reverse=True)
    grand = sum(v["size"] for _, v in ranked) or 1
    items = [kv for kv in ranked[:top] if kv[1]["size"] / grand >= 0.002]
    total = sum(v["size"] for _, v in items) or 1

    W = 400
    H = 60 + ((len(items) + 1) // 2) * 22 + 20
    BAR_X, BAR_W, BAR_Y = 25, W - 50, 58
    COL = BAR_W / 2

    bar, legend, x = "", "", float(BAR_X)
    for i, (name, meta) in enumerate(items):
        pct = meta["size"] / total * 100
        w = BAR_W * pct / 100
        color = meta["color"] or P["muted"]
        radius = 'rx="2" ry="2"' if i in (0, len(items) - 1) else ""
        bar += (
            f'<rect x="{x:.1f}" y="{BAR_Y}" width="{w:.1f}" height="8" {radius} fill="{color}">'
            f'<animate attributeName="width" values="0;{w:.1f}" dur="0.7s" '
            f'begin="{0.1 + i * 0.07:.2f}s" fill="freeze"/></rect>'
        )
        x += w

        col, row = i % 2, i // 2
        lx = BAR_X + col * COL
        ly = BAR_Y + 34 + row * 22
        legend += (
            f'<g opacity="1"><circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 17}" y="{ly}" font-family="{MONO}" font-size="11" '
            f'fill="{P["fg"]}">{name}</text>'
            f'<text x="{lx + COL - 14:.0f}" y="{ly}" text-anchor="end" font-family="{MONO}" '
            f'font-size="11" fill="{P["muted"]}">{pct:.1f}%</text>'
            f'<animate attributeName="opacity" values="0;1" dur="0.5s" '
            f'begin="{0.2 + i * 0.07:.2f}s" fill="freeze"/></g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" aria-label="Most used languages">
  <title>Most used languages</title>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" ry="6" fill="none" stroke="{P['border']}"/>
  <text x="25" y="34" font-family="{SANS}" font-size="16" font-weight="600" fill="{P['accent']}">Most Used Languages</text>
  <rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" height="8" rx="2" ry="2" fill="{P['track']}"/>
  {bar}
  {legend}
</svg>
"""


if __name__ == "__main__":
    login = sys.argv[1]
    out = Path(sys.argv[2])
    token = os.environ["GITHUB_TOKEN"]

    data = collect(login, token)
    out.mkdir(parents=True, exist_ok=True)
    for mode, P in PRIMER.items():
        (out / f"stats-{mode}.svg").write_text(stats_card(data, P), encoding="utf-8")
        (out / f"top-langs-{mode}.svg").write_text(langs_card(data, P), encoding="utf-8")
    print(
        f"rendered stats for {login}: {data['stars']} stars, {data['commits']} commits, "
        f"{len(data['langs'])} languages"
    )
