#!/usr/bin/env python3
"""Render site/og.png, the social card, from data/derived.json.

The only script in this repo that needs a dependency:
    pip install pillow
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

SITE_URL = "rackrate.dev"

WIDTH, HEIGHT = 1200, 630

# Same palette as site/template.html. Keep these two in sync by hand; the
# card is rendered by a script with no access to the page's CSS.
BG = "#0A0E15"
PANEL = "#111825"
INK = "#EAEEF5"
INK_DIM = "#A3B0C4"
INK_FAINT = "#67768D"
ADJ = "#FFB020"
MEASURED = "#45D97F"
API = "#5C6A80"
RULE = "#1D2735"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def load_font(candidates, size):
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    derived = json.loads((DATA / "derived.json").read_text())
    routes = derived.get("best_routes", [])
    if not routes:
        raise SystemExit("make_og.py: derived.json has no best_routes, run compute.py first")

    cheapest = min(routes, key=lambda r: r["cost_per_task_usd"])
    top_scorer = max(routes, key=lambda r: r["score_pct"])

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    h1 = load_font(FONT_BOLD_CANDIDATES, 64)
    h2 = load_font(FONT_CANDIDATES, 28)
    mono = load_font(MONO_CANDIDATES, 30)
    small = load_font(FONT_CANDIDATES, 22)

    margin = 80
    draw.text((margin, 70), "Rack Rate", font=h1, fill=INK)
    draw.text(
        (margin, 150),
        "API list pricing is the rack rate. Nobody pays it.",
        font=h2,
        fill=INK_DIM,
    )

    draw.line([(margin, 220), (WIDTH - margin, 220)], fill=RULE, width=1)

    def stat_block(y, label, model, value, value_color):
        draw.text((margin, y), label, font=small, fill=INK_FAINT)
        draw.text((margin, y + 35), model, font=h2, fill=INK)
        draw.text((margin, y + 85), value, font=mono, fill=value_color)

    stat_block(
        260, "CHEAPEST ROUTE", cheapest["model_name"],
        f"${cheapest['cost_per_task_usd']:.3f} / task on {cheapest['plan_name']}", ADJ,
    )
    stat_block(
        420, "TOP SCORER", top_scorer["model_name"],
        f"{top_scorer['score_pct']:.0f}% · ${top_scorer['cost_per_task_usd']:.3f} / task", MEASURED,
    )

    draw.text((margin, HEIGHT - 90), SITE_URL, font=h2, fill=API)

    out_path = SITE / "og.png"
    img.save(out_path)
    print(f"make_og.py: wrote {out_path}")


if __name__ == "__main__":
    main()
