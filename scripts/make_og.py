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

SITE_URL = "rack-rate-flax.vercel.app"

WIDTH, HEIGHT = 1200, 630

# Same palette as site/template.html. Keep these two in sync by hand; the
# card is rendered by a script with no access to the page's CSS.
BG = "#121310"
PANEL = "#1b1d18"
INK = "#f2efe6"
INK_DIM = "#b8bbae"
INK_FAINT = "#999e8e"
ADJ = "#eeb94e"
MEASURED = "#aecf99"
API = "#929b88"
RULE = "#36392f"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
MONO_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
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
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    headline = load_font(FONT_CANDIDATES, 78)
    brand = load_font(FONT_BOLD_CANDIDATES, 26)
    body = load_font(FONT_CANDIDATES, 25)
    small = load_font(FONT_CANDIDATES, 18)
    number = load_font(FONT_CANDIDATES, 43)
    mono = load_font(MONO_CANDIDATES, 13)

    margin = 64
    draw.rectangle((64, 40, 96, 72), outline=ADJ, width=1)
    draw.line([(71, 49), (83, 49), (90, 56), (83, 63), (71, 63), (71, 49)], fill=ADJ, width=2)
    draw.ellipse((74, 54, 77, 57), fill=ADJ)
    draw.text((110, 40), "Rack Rate.", font=brand, fill=INK)
    draw.text((870, 49), "THE AI CODING COST INDEX", font=mono, fill=INK_DIM)
    draw.line([(margin, 99), (WIDTH - margin, 99)], fill=RULE)

    for y, line, color in [(145, "Stop paying", INK), (224, "sticker price", ADJ), (303, "for AI coding.", INK)]:
        draw.text((margin, y), line, font=headline, fill=color)
    draw.text((margin, 425), "Compare API costs and coding plans", font=body, fill=INK_DIM)
    draw.text((margin, 460), "for the work you actually do.", font=body, fill=INK)

    draw.line([(810, 147), (810, 494)], fill=RULE)
    for y, value, label in [
        (147, derived["generated_from"]["models"], "benchmark models"),
        (260, derived["generated_from"]["plans"], "coding plans"),
        (373, derived["generated_from"]["task_count"], "coding tasks"),
    ]:
        draw.text((858, y), str(value), font=number, fill=ADJ)
        draw.text((858, y + 53), label, font=small, fill=INK_DIM)

    draw.line([(margin, 543), (WIDTH - margin, 543)], fill=RULE)
    draw.text((margin, 568), "Open data. Traceable estimates.", font=small, fill=INK_DIM)
    draw.text((830, 568), SITE_URL, font=small, fill=INK_DIM)

    out_path = SITE / "og.png"
    img.save(out_path)
    print(f"make_og.py: wrote {out_path}")


if __name__ == "__main__":
    main()
