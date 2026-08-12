"""Generates the animated SVG assets for the profile README.

Design rules:
  - GitHub Primer colour tokens only, so the art matches the page it sits on.
  - Transparent backgrounds and no borders, so there is no visible card edge.
  - Flat / matte: no gradients, glows, blurs or shine.
  - A dark and a light build of each piece, paired with <picture> in the README.

Run: python3 tools/generate_svgs.py [output_dir]
"""
import math
import random
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"

# https://primer.style/foundations/color
PRIMER = {
    "dark": {
        "fg": "#e6edf3",        # fg.default
        "muted": "#8b949e",     # fg.muted
        "border": "#30363d",    # border.default
        "wire": "#6e7681",      # fg.subtle
        "accent": "#2f81f7",    # accent.fg
        "done": "#a371f7",      # done.fg
        "success": "#3fb950",   # success.fg
    },
    "light": {
        "fg": "#1f2328",
        "muted": "#59636e",
        "border": "#d1d9e0",
        "wire": "#6e7781",
        "accent": "#0969da",
        "done": "#8250df",
        "success": "#1a7f37",
    },
}

MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# hero — text left, an MLP that wires itself up and fires on the right
# --------------------------------------------------------------------------
def hero(P):
    rng = random.Random(11)
    W, H = 1000, 290
    xs = [565, 690, 815, 940]
    sizes = [4, 6, 5, 3]
    colors = [P["muted"], P["accent"], P["done"], P["success"]]
    GAP, CY = 38, 142

    layers = []
    for n in sizes:
        total = (n - 1) * GAP
        layers.append([CY - total / 2 + i * GAP for i in range(n)])

    edges, nodes, pulses = [], [], []

    for li in range(len(layers) - 1):
        base = 0.35 + li * 0.55
        for ay in layers[li]:
            for by in layers[li + 1]:
                x1, y1, x2, y2 = xs[li], ay, xs[li + 1], by
                length = math.hypot(x2 - x1, y2 - y1)
                begin = base + rng.uniform(0, 0.3)
                op = round(rng.uniform(0.32, 0.7), 3)
                edges.append(
                    f'<line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}" '
                    f'stroke="{P["wire"]}" stroke-width="1" opacity="0" '
                    f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}">'
                    f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" '
                    f'dur="1.05s" begin="{begin:.2f}s" fill="freeze"/>'
                    f'<animate attributeName="opacity" from="0" to="{op}" '
                    f'dur="0.9s" begin="{begin:.2f}s" fill="freeze"/>'
                    f"</line>"
                )
                if rng.random() < 0.3:
                    d, on = 5.0, 0.2
                    pb = 2.6 + li * 0.42 + rng.uniform(0, 0.5)
                    pulses.append(
                        f'<circle r="2.4" fill="{colors[li + 1]}" opacity="0">'
                        f'<animateMotion dur="{d}s" begin="{pb:.2f}s" repeatCount="indefinite" '
                        f'calcMode="linear" keyPoints="0;1;1" keyTimes="0;{on};1" '
                        f'path="M{x1},{y1:.1f} L{x2},{y2:.1f}"/>'
                        f'<animate attributeName="opacity" values="0;1;1;0;0" '
                        f'keyTimes="0;0.03;{on * 0.85:.3f};{on};1" '
                        f'dur="{d}s" begin="{pb:.2f}s" repeatCount="indefinite"/>'
                        f"</circle>"
                    )

    for li, (x, ys) in enumerate(zip(xs, layers)):
        for k, y in enumerate(ys):
            b = 0.15 + li * 0.55 + k * 0.05
            c = colors[li]
            nodes.append(
                f'<circle cx="{x}" cy="{y:.1f}" r="0" fill="{c}">'
                f'<animate attributeName="r" values="0;6.4;4.6" keyTimes="0;0.6;1" '
                f'dur="0.55s" begin="{b:.2f}s" fill="freeze"/>'
                f"</circle>"
            )
            if rng.random() < 0.35:
                rb = b + rng.uniform(0, 2)
                nodes.append(
                    f'<circle cx="{x}" cy="{y:.1f}" r="4.6" fill="none" stroke="{c}" stroke-width="1">'
                    f'<animate attributeName="r" values="4.6;15" dur="3.4s" '
                    f'begin="{rb:.2f}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values="0.6;0" dur="3.4s" '
                    f'begin="{rb:.2f}s" repeatCount="indefinite"/>'
                    f"</circle>"
                )

    caps = "".join(
        f'<text x="{x}" y="264" text-anchor="middle" font-family="{MONO}" '
        f'font-size="9" letter-spacing="1.4" fill="{P["muted"]}" opacity="0">{t}'
        f'<animate attributeName="opacity" from="0" to="1" dur="1s" '
        f'begin="{0.4 + i * 0.55:.2f}s" fill="freeze"/></text>'
        for i, (x, t) in enumerate(zip(xs, ["input", "hidden", "hidden", "output"]))
    )

    tagline = "Data Science · Applied AI · Graph Learning"
    tl_len, x0 = 396, 40

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" aria-label="Ishaan Potle">
  <title>Ishaan Potle — {esc(tagline)}</title>
  <defs>
    <clipPath id="type">
      <rect x="{x0 - 4}" y="168" width="0" height="28">
        <animate attributeName="width" values="0;{tl_len + 8};{tl_len + 8};0;0"
                 keyTimes="0;0.40;0.86;0.97;1" dur="11s" begin="2.2s" repeatCount="indefinite"/>
      </rect>
    </clipPath>
  </defs>

  <g>{{edges}}</g>
  <g>{{pulses}}</g>
  <g>{{nodes}}</g>
  {{caps}}

  <rect x="{x0}" y="70" width="0" height="3" fill="{P['accent']}">
    <animate attributeName="width" values="0;52" dur="0.7s" fill="freeze"/>
  </rect>

  <text x="{x0}" y="138" font-family="{SANS}" font-size="52" font-weight="700" letter-spacing="0.3">
    <tspan fill="{P['fg']}">Ishaan</tspan><tspan fill="{P['accent']}"> Potle</tspan>
  </text>

  <g clip-path="url(#type)">
    <text x="{x0}" y="189" textLength="{tl_len}" lengthAdjust="spacingAndGlyphs"
          font-family="{MONO}" font-size="16" fill="{P['muted']}">{esc(tagline)}</text>
  </g>
  <rect y="173" width="8" height="21" fill="{P['accent']}" opacity="0">
    <animate attributeName="x" values="{x0};{x0 + tl_len};{x0 + tl_len};{x0};{x0}"
             keyTimes="0;0.40;0.86;0.97;1" dur="11s" begin="2.2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0;1" dur="0.1s" begin="2.2s" fill="freeze"/>
    <animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1"
             dur="1.15s" begin="2.3s" repeatCount="indefinite"/>
  </rect>

  <text x="{x0}" y="225" font-family="{MONO}" font-size="13" fill="{P['muted']}" opacity="0">M.S. Data Science @ Stony Brook University
    <animate attributeName="opacity" from="0" to="1" dur="1.2s" begin="3.4s" fill="freeze"/>
  </text>
</svg>
""".replace("{edges}", "".join(edges)).replace("{pulses}", "".join(pulses)).replace(
        "{nodes}", "".join(nodes)
    ).replace("{caps}", caps)


# --------------------------------------------------------------------------
# divider — hairline with a solid segment sliding along it.
# Theme-agnostic: neutral grey reads on both canvases, so only one file.
# --------------------------------------------------------------------------
def divider():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="10" viewBox="0 0 1000 10" fill="none" role="img" aria-label="">
  <defs><clipPath id="strip"><rect y="4" width="1000" height="2"/></clipPath></defs>
  <rect y="4.5" width="1000" height="1" fill="#8b949e" opacity="0.35"/>
  <g clip-path="url(#strip)">
    <rect y="4" width="140" height="1" fill="#2f81f7">
      <animate attributeName="x" values="-140;1000" dur="7s" repeatCount="indefinite"/>
    </rect>
  </g>
</svg>
"""


# --------------------------------------------------------------------------
# footer — sparse graph that keeps firing around the sign-off
# --------------------------------------------------------------------------
def footer(P):
    rng = random.Random(23)
    W, H = 1000, 180
    box = (280, 720, 18, 100)  # keep the sign-off text clear of the graph

    def blocked(x, y):
        return box[0] < x < box[1] and box[2] < y < box[3]

    pts, tries = [], 0
    while len(pts) < 24 and tries < 6000:
        tries += 1
        x, y = rng.uniform(24, W - 24), rng.uniform(20, H - 18)
        if blocked(x, y):
            continue
        if all(math.hypot(x - a, y - b) > 66 for a, b in pts):
            pts.append((x, y))

    pairs = []
    for i, (x1, y1) in enumerate(pts):
        for j, (x2, y2) in enumerate(pts[i + 1:], i + 1):
            d = math.hypot(x2 - x1, y2 - y1)
            if d < 118 and not blocked((x1 + x2) / 2, (y1 + y2) / 2):
                pairs.append((i, j, d))
    pairs.sort(key=lambda t: t[2])

    edges, pulses = [], []
    for i, j, d in pairs:
        x1, y1 = pts[i]
        x2, y2 = pts[j]
        op = round(max(0.22, 0.7 - d / 260), 3)
        edges.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{P["wire"]}" stroke-width="1" opacity="{op}">'
            f'<animate attributeName="opacity" values="{op};{min(1, op * 1.7):.3f};{op}" '
            f'dur="{rng.uniform(4, 9):.1f}s" begin="-{rng.uniform(0, 6):.1f}s" repeatCount="indefinite"/>'
            f"</line>"
        )
        if rng.random() < 0.22:
            dur = rng.uniform(4.5, 7.0)
            on = 1.0 / dur
            off = rng.uniform(0, 5)
            pulses.append(
                f'<circle r="2" fill="{P["accent"]}" opacity="0">'
                f'<animateMotion dur="{dur:.1f}s" begin="-{off:.1f}s" repeatCount="indefinite" '
                f'calcMode="linear" keyPoints="0;1;1" keyTimes="0;{on:.3f};1" '
                f'path="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}"/>'
                f'<animate attributeName="opacity" values="0;1;1;0;0" '
                f'keyTimes="0;0.04;{on * 0.8:.3f};{on:.3f};1" '
                f'dur="{dur:.1f}s" begin="-{off:.1f}s" repeatCount="indefinite"/>'
                f"</circle>"
            )

    nodes = []
    for x, y in pts:
        c = rng.choice([P["accent"], P["done"], P["success"], P["muted"]])
        r = rng.uniform(2.0, 3.4)
        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}" opacity="0.8">'
            f'<animate attributeName="opacity" values="0.5;1;0.5" '
            f'dur="{rng.uniform(3, 7):.1f}s" begin="-{rng.uniform(0, 5):.1f}s" repeatCount="indefinite"/>'
            f"</circle>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" aria-label="Thanks for visiting">
  <title>Thanks for visiting</title>
  <g>{''.join(edges)}</g>
  <g>{''.join(pulses)}</g>
  <g>{''.join(nodes)}</g>
  <text x="500" y="62" text-anchor="middle" font-family="{SANS}" font-size="26" font-weight="600"
        fill="{P['fg']}">Thanks for visiting</text>
  <text x="500" y="88" text-anchor="middle" font-family="{MONO}" font-size="13"
        fill="{P['muted']}">open to collaborating on ML, graphs &amp; systems</text>
</svg>
"""


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    out.mkdir(parents=True, exist_ok=True)

    (out / "divider.svg").write_text(divider(), encoding="utf-8")
    print("wrote divider.svg")

    for mode, P in PRIMER.items():
        for name, fn in (("hero", hero), ("footer", footer)):
            svg = fn(P)
            (out / f"{name}-{mode}.svg").write_text(svg, encoding="utf-8")
            print(f"wrote {name}-{mode}.svg  ({len(svg) / 1024:.1f} KB)")
