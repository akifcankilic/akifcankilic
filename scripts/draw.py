"""Draws the SVGs used in the profile README.

    python scripts/draw.py

Colours come from kilim weaving (madder, saffron, indigo, walnut) on the
dark navy of digitalyoruk.com. Fonts are subset per file and embedded, since
GitHub serves README images through a proxy that blocks webfont requests.

Scholar numbers are updated by hand: Scholar blocks requests from CI.
"""

import base64
import io
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"

SCHOLAR = {"citations": 21, "h-index": 2, "i10-index": 1, "checked": "Oct 2026"}

NAVY = "#13131e"
NAVY_2 = "#1c1c2b"
CREAM = "#efe6d2"
MUTED = "#9a9ab8"
MADDER = "#c2412d"
SAFFRON = "#e3a72f"
INDIGO = "#6366f1"
TEAL = "#2f8f7f"
WALNUT = "#7a4a2a"
KILIM = [MADDER, SAFFRON, INDIGO, TEAL]


# --- fonts ------------------------------------------------------------------

def font_face(chars, weights=(400, 700)):
    rules = []
    for w in weights:
        f = TTFont(FONTS / f"inconsolata-{w}.woff2")
        opts = subset.Options()
        opts.flavor = "woff2"
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(set(chars))))
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rules.append(f"@font-face{{font-family:inc;font-weight:{w};"
                     f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "".join(rules)


def width(s, size):
    """Inconsolata is monospaced at half an em."""
    return len(s) * size * 0.5


def svg(w, h, chars, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        f"<style>{font_face(chars)} text{{font-family:inc,Consolas,monospace}}</style>\n"
        f"{body}\n</svg>\n"
    )


def text(x, y, s, size, fill, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>')


# --- kilim ------------------------------------------------------------------

def kilim_band(y, w, h=28, offset=0):
    """A woven strip: stepped diamonds alternating colours, hooks in between."""
    u = h * 1.6
    p = [f'<rect x="0" y="{y}" width="{w}" height="{h}" fill="{WALNUT}"/>']
    n = int(w / u) + 2
    for i in range(-1, n):
        cx = i * u + u / 2
        cy = y + h / 2
        a = KILIM[(i + offset) % len(KILIM)]
        b = KILIM[(i + offset + 2) % len(KILIM)]
        r = h / 2 - 2
        p.append(f'<path d="M{cx} {cy - r} L{cx + r} {cy} L{cx} {cy + r} L{cx - r} {cy} Z" fill="{a}"/>')
        r2 = r * 0.55
        p.append(f'<path d="M{cx} {cy - r2} L{cx + r2} {cy} L{cx} {cy + r2} L{cx - r2} {cy} Z" fill="{b}"/>')
        p.append(f'<rect x="{cx - 2}" y="{cy - 2}" width="4" height="4" fill="{CREAM}"/>')
        # hooks between diamonds
        hx = cx + u / 2
        p.append(f'<path d="M{hx - 4} {y + 3} L{hx} {y + 7} L{hx + 4} {y + 3} M{hx - 4} {y + h - 3} '
                 f'L{hx} {y + h - 7} L{hx + 4} {y + h - 3}" stroke="{CREAM}" stroke-width="1.6" fill="none"/>')
    p.append(f'<rect x="0" y="{y}" width="{w}" height="1.5" fill="{CREAM}" opacity="0.5"/>')
    p.append(f'<rect x="0" y="{y + h - 1.5}" width="{w}" height="1.5" fill="{CREAM}" opacity="0.5"/>')
    return "\n".join(p)


# --- pieces -----------------------------------------------------------------

def header():
    W, H = 880, 280
    name = "Akif Can Kılıç"
    role = "engineer · researcher · generalist"
    where = "Frankfurt"
    line1 = "air cargo by day  —  Digital Yörük the rest of the time"
    p = [
        f'<rect width="{W}" height="{H}" rx="14" fill="{NAVY}"/>',
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>',
        f'<g clip-path="url(#c)">',
        kilim_band(0, W, 30),
        kilim_band(H - 30, W, 30, offset=1),
        "</g>",
        text(56, 122, name, 60, CREAM, 700),
        f'<rect x="58" y="140" width="{width(name, 60) - 4}" height="5" fill="{MADDER}"/>',
        f'<rect x="58" y="140" width="{(width(name, 60) - 4) * 0.5}" height="5" fill="{SAFFRON}"/>',
        f'<rect x="58" y="140" width="{(width(name, 60) - 4) * 0.25}" height="5" fill="{INDIGO}"/>',
        text(56, 184, role, 24, SAFFRON, 700),
        text(56, 220, line1, 19, MUTED),
        text(W - 56, 122, where, 20, MUTED, 400, "end"),
        f'<circle cx="{W - 56 - width(where, 20) - 14}" cy="115" r="5" fill="{MADDER}"/>',
    ]
    return svg(W, H, name + role + where + line1, "\n".join(p))


def stats():
    W, H = 880, 150
    tiles = [
        (str(SCHOLAR["citations"]), "citations", MADDER),
        (str(SCHOLAR["h-index"]), "h-index", INDIGO),
        (str(SCHOLAR["i10-index"]), "i10-index", TEAL),
    ]
    gap = 16
    tw = (W - gap * 2 - 220) / 3
    p = [f'<rect width="{W}" height="{H}" rx="14" fill="{NAVY}"/>']
    for i, (num, label, col) in enumerate(tiles):
        x = i * (tw + gap)
        p.append(f'<rect x="{x}" y="0" width="{tw}" height="{H}" rx="14" fill="{col}"/>')
        p.append(f'<path d="M{x + tw - 34} 14 l10 10 l-10 10 l-10 -10 Z" fill="{CREAM}" opacity="0.35"/>')
        p.append(text(x + 24, 92, num, 64, CREAM, 700))
        p.append(text(x + 26, 126, label, 20, CREAM, 700))
    sx = 3 * tw + 2 * gap + 24
    note1, note2, note3 = "Google Scholar", "counted by hand,", f"last checked {SCHOLAR['checked']}"
    p.append(text(sx, 62, note1, 22, SAFFRON, 700))
    p.append(text(sx, 94, note2, 17, MUTED))
    p.append(text(sx, 118, note3, 17, MUTED))
    chars = "".join(t[0] + t[1] for t in tiles) + note1 + note2 + note3
    return svg(W, H, chars, "\n".join(p))


def timeline():
    stops = [
        ("Çelebi Ground Handling", "aircraft ops → sales & marketing", MADDER),
        ("Istanbul Kültür University", "research assistant, IE · 2019–2022", SAFFRON),
        ("Galatasaray University", "MSc thesis · ML on wellbeing data", INDIGO),
        ("Invisible Technologies", "AI trainer · 20+ projects, ~2.5 yrs", TEAL),
        ("Çelebi Cargo, Frankfurt", "sales & marketing · now", MADDER),
    ]
    W, row, top = 880, 62, 34
    H = top + row * (len(stops) - 1) + 44
    p = [f'<rect width="{W}" height="{H}" rx="14" fill="{NAVY}"/>']
    x = 60
    for i in range(len(stops) - 1):
        y1, y2 = top + i * row, top + (i + 1) * row
        p.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{stops[i + 1][2]}" stroke-width="3" opacity="0.6"/>')
    chars = ""
    for i, (title, sub, col) in enumerate(stops):
        y = top + i * row
        p.append(f'<path d="M{x} {y - 11} L{x + 11} {y} L{x} {y + 11} L{x - 11} {y} Z" fill="{col}"/>')
        p.append(f'<rect x="{x - 2.5}" y="{y - 2.5}" width="5" height="5" fill="{CREAM}"/>')
        p.append(text(x + 30, y + 2, title, 21, CREAM, 700))
        p.append(text(x + 30, y + 24, sub, 16, MUTED))
        chars += title + sub
    return svg(W, H, chars, "\n".join(p))


def divider():
    W, H = 880, 18
    return svg(W, H, "", kilim_band(0, W, H))


def pill(label, col):
    size, pad, H = 18, 18, 40
    W = round(width(label, size) + pad * 2 + 18)
    p = [
        f'<rect width="{W}" height="{H}" rx="20" fill="{col}"/>',
        f'<path d="M{pad + 4} {H / 2 - 5} l5 5 l-5 5 l-5 -5 Z" fill="{CREAM}"/>',
        text(pad + 18, H / 2 + 6, label, size, CREAM, 700),
    ]
    return svg(W, H, label, "\n".join(p))


def main():
    out = ASSETS
    (out / "header.svg").write_text(header())
    (out / "stats.svg").write_text(stats())
    (out / "timeline.svg").write_text(timeline())
    (out / "divider.svg").write_text(divider())
    links = ASSETS / "links"
    links.mkdir(exist_ok=True)
    for name, label, col in [
        ("email", "email", MADDER),
        ("linkedin", "linkedin", INDIGO),
        ("youtube", "youtube", MADDER),
        ("skool", "skool", SAFFRON),
        ("scholar", "scholar", TEAL),
        ("site", "digitalyoruk.com", WALNUT),
    ]:
        (links / f"{name}.svg").write_text(pill(label, col))


if __name__ == "__main__":
    main()
