"""Draws the notebook header and the little paper badges for the profile README.

    python scripts/draw.py           # redraw from assets/scholar.json
    python scripts/draw.py --fetch   # refresh numbers from Google Scholar first

Everything is plain SVG. The handwriting font is subset per file and embedded,
because GitHub serves README images through a proxy that blocks webfont requests.
Wobble is seeded by the text it surrounds, so redrawing never produces a diff
unless something actually changed.
"""

import base64
import io
import json
import random
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT = ASSETS / "fonts" / "caveat-500.woff2"
DATA = ASSETS / "scholar.json"
SCHOLAR_ID = "2-mR1FwAAAAJ"

INK = "#2a2a35"
PENCIL = "#6b6b78"
RED = "#c8553d"
PAPER = "#fbf7ec"
RULE = "#c9d8e8"
MARKER = "#ffe066"


# --- font -----------------------------------------------------------------

_font = TTFont(FONT)
_cmap = _font.getBestCmap()
_hmtx = _font["hmtx"]
_upm = _font["head"].unitsPerEm


def text_width(s, size):
    return sum(_hmtx[_cmap[ord(c)]][0] for c in s if ord(c) in _cmap) * size / _upm


def font_face(chars):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    sub = subset.Subsetter(opts)
    f = TTFont(FONT)
    sub.populate(text="".join(sorted(set(chars))))
    sub.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:hand;src:url(data:font/woff2;base64,{b64}) format('woff2')}}"


# --- pen ------------------------------------------------------------------

def stroke(rng, x1, y1, x2, y2, wobble=1.2):
    """One slightly bowed line, like drawing without a ruler."""
    mx = (x1 + x2) / 2 + rng.uniform(-wobble, wobble)
    my = (y1 + y2) / 2 + rng.uniform(-wobble, wobble)
    j = lambda: rng.uniform(-wobble * 0.6, wobble * 0.6)
    return f"M{x1 + j():.1f} {y1 + j():.1f} Q{mx:.1f} {my:.1f} {x2 + j():.1f} {y2 + j():.1f}"


def box(rng, x, y, w, h, wobble=1.2):
    """Rectangle drawn twice, corners overshooting a bit."""
    d = []
    for _ in range(2):
        o = lambda: rng.uniform(-2.5, 1.5)
        d.append(stroke(rng, x + o(), y, x + w - o(), y, wobble))
        d.append(stroke(rng, x + w, y + o(), x + w, y + h - o(), wobble))
        d.append(stroke(rng, x + w - o(), y + h, x + o(), y + h, wobble))
        d.append(stroke(rng, x, y + h - o(), x, y + o(), wobble))
    return " ".join(d)


def arrow(rng, x1, y1, x2, y2):
    """Small outward arrow (↗), the font has no glyph for it."""
    head = 5
    return " ".join([
        stroke(rng, x1, y1, x2, y2, 0.6),
        stroke(rng, x2 - head, y2 + 0.5, x2, y2, 0.4),
        stroke(rng, x2, y2, x2 - 0.5, y2 + head, 0.4),
    ])


def svg(w, h, chars, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        f"<style>{font_face(chars)} text{{font-family:hand,'Comic Sans MS',cursive}}</style>\n"
        f"{body}\n</svg>\n"
    )


# --- pieces ---------------------------------------------------------------

def badge(label, note=None, link_arrow=False, highlight=None):
    """A torn-off paper tag. `highlight` is a substring of label to mark yellow."""
    rng = random.Random(label)
    size, pad = 24, 16
    h = 64 if note else 46
    tw = text_width(label, size)
    w = round(max(tw + (14 if link_arrow else 0), text_width(note or "", 15)) + pad * 2) + 6
    W, H = w + 6, h + 6
    base = 3 + (34 if note else h * 0.68)
    tilt = rng.uniform(-1.2, 1.2)
    parts = [f'<g transform="rotate({tilt:.2f} {W / 2:.0f} {h / 2:.0f})">']
    parts.append(f'<rect x="3" y="3" width="{w}" height="{h}" fill="{PAPER}"/>')
    if highlight and highlight in label:
        hx = 3 + pad + text_width(label[: label.index(highlight)], size)
        hw = text_width(highlight, size)
        parts.append(
            f'<path d="{stroke(rng, hx - 3, base - 8, hx + hw + 3, base - 10, 1.5)}" '
            f'stroke="{MARKER}" stroke-width="14" stroke-linecap="round" fill="none" opacity="0.85"/>'
        )
    parts.append(f'<path d="{box(rng, 3, 3, w, h)}" stroke="{INK}" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
    parts.append(f'<text x="{3 + pad}" y="{base:.1f}" font-size="{size}" fill="{INK}">{label}</text>')
    if link_arrow:
        ax = 3 + pad + tw + 6
        parts.append(f'<path d="{arrow(rng, ax, base - 4, ax + 9, base - 16)}" stroke="{INK}" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
    if note:
        parts.append(f'<text x="{3 + pad}" y="{h - 6}" font-size="15" fill="{PENCIL}">{note}</text>')
    parts.append("</g>")
    return svg(W, H, label + (note or ""), "\n".join(parts))


def header():
    rng = random.Random("akif")
    W, H = 860, 205
    line = 34
    top = 62
    p = [f'<rect width="{W}" height="{H}" rx="3" fill="{PAPER}"/>']
    for i in range(int((H - top) / line) + 1):
        y = top + i * line
        p.append(f'<path d="{stroke(rng, 0, y, W, y, 0.6)}" stroke="{RULE}" stroke-width="1"/>')
    p.append(f'<path d="{stroke(rng, 70, 0, 70, H, 0.8)}" stroke="{RED}" stroke-width="1.4" opacity="0.7"/>')
    for y in (45, 102, 160):
        p.append(f'<circle cx="28" cy="{y}" r="9" fill="#e9e3d3"/>')

    name = "Akif Can Kilic"
    p.append(f'<text x="96" y="{top + line - 8}" font-size="54" fill="{INK}">{name}</text>')
    nw = text_width(name, 54)
    p.append(f'<path d="{stroke(rng, 98, top + line + 2, 96 + nw + 8, top + line - 2, 2.5)}" stroke="{RED}" stroke-width="2.2" fill="none" stroke-linecap="round"/>')

    l1 = "air cargo · contracts · invoices · the gaps between them"
    p.append(f'<text x="100" y="{top + 2 * line - 8}" font-size="27" fill="{INK}">{l1}</text>')

    a = "how it's written in procedures"
    b = "how it's really done"
    y3 = top + 3 * line - 8
    p.append(f'<text x="100" y="{y3}" font-size="27" fill="{PENCIL}">{a}</text>')
    aw = text_width(a, 27)
    p.append(f'<path d="{stroke(rng, 98, y3 - 8, 104 + aw, y3 - 10, 1.5)}" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>')
    bx = 100 + aw + 36
    p.append(f'<path d="{arrow(rng, bx - 26, y3 - 4, bx - 8, y3 - 14)}" stroke="{RED}" stroke-width="1.8" fill="none" stroke-linecap="round"/>')
    p.append(f'<text x="{bx}" y="{y3}" font-size="27" fill="{INK}">{b}</text>')

    note = "mostly internal, by design."
    p.append(f'<text x="{W - 24}" y="{H - 16}" font-size="19" fill="{PENCIL}" text-anchor="end" transform="rotate(-2 {W - 24} {H - 16})">{note}</text>')

    return svg(W, H, name + l1 + a + b + note, "\n".join(p))


# --- scholar --------------------------------------------------------------

def fetch_scholar():
    req = urllib.request.Request(
        f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en",
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"},
    )
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    # stats table: [citations all, since, h-index all, since, i10 all, since]
    cells = [int(n) for n in re.findall(r'class="gsc_rsb_std">(\d+)<', html)]
    if len(cells) < 6:
        raise RuntimeError("stats table not found (captcha?)")
    return {"citations": cells[0], "h_index": cells[2], "i10_index": cells[4],
            "updated": date.today().isoformat()}


def main():
    data = json.loads(DATA.read_text()) if DATA.exists() else {}
    if "--fetch" in sys.argv:
        try:
            data = fetch_scholar()
            DATA.write_text(json.dumps(data, indent=2) + "\n")
        except Exception as e:  # keep yesterday's numbers rather than failing the job
            print(f"scholar fetch failed, keeping previous numbers: {e}", file=sys.stderr)

    out = ASSETS / "badges"
    out.mkdir(parents=True, exist_ok=True)
    (ASSETS / "header.svg").write_text(header())
    (out / "linkedin.svg").write_text(badge("linkedin", link_arrow=True))
    (out / "scholar.svg").write_text(badge("google scholar", link_arrow=True))

    cites = data.get("citations")
    when = data.get("updated")
    note = f"as of {date.fromisoformat(when).strftime('%d %b %Y').lower()}" if when else "not counted yet"
    if cites is None:
        (out / "citations.svg").write_text(badge("cited ? times", note=note))
    else:
        (out / "citations.svg").write_text(badge(f"cited {cites} times", note=note, highlight=str(cites)))
    h = data.get("h_index")
    (out / "h-index.svg").write_text(badge(f"h-index {h if h is not None else '?'}"))


if __name__ == "__main__":
    main()
