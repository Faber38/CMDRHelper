#!/usr/bin/env python3
"""Render the German CMDRHelper README intro test image with Pillow."""

from __future__ import annotations

import argparse
import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "cmdrhelper/assets/readme/cmdrhelper_readme_master.png"
TEXT_DIR = ROOT / "assets/readme/text"
OUTPUT_DIR = ROOT / "cmdrhelper/assets/readme"

FONT_REGULAR = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
FONT_BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FONT_CONDENSED = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf")
FONT_CONDENSED_BOLD = Path(
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
)


@dataclass(frozen=True)
class TextArea:
    box: tuple[int, int, int, int]
    font: Path
    max_size: int
    min_size: int
    fill: tuple[int, int, int, int]
    align: str = "left"
    anchor: str = "mm"
    spacing: int = 4
    background: tuple[int, int, int, int] | None = None
    outline: tuple[int, int, int, int] | None = None
    radius: int = 18
    padding: int = 14
    stroke_width: int = 0
    stroke_fill: tuple[int, int, int, int] | None = None


AREAS = {
    "speech_commander": TextArea(
        (24, 20, 555, 154), FONT_CONDENSED, 26, 17, (30, 24, 18, 255),
        align="center", background=(245, 238, 218, 235),
        outline=(213, 125, 34, 255), radius=24, padding=14,
    ),
    "speech_helper": TextArea(
        (1020, 22, 1510, 140), FONT_CONDENSED_BOLD, 25, 17,
        (225, 247, 255, 255), align="center",
        background=(5, 27, 41, 225), outline=(40, 218, 255, 255),
        radius=24, padding=13,
    ),
    "speech_robot": TextArea(
        (1195, 150, 1506, 260), FONT_CONDENSED_BOLD, 23, 16,
        (232, 248, 250, 255), align="center",
        background=(8, 31, 42, 220), outline=(255, 151, 25, 255),
        radius=22, padding=12,
    ),
    "panel_jump": TextArea(
        (690, 194, 968, 250), FONT_CONDENSED_BOLD, 20, 14,
        (145, 238, 255, 255), align="center", padding=3,
    ),
    "panel_bio": TextArea(
        (690, 267, 968, 323), FONT_CONDENSED, 19, 13,
        (145, 238, 255, 255), align="center", padding=3,
    ),
    "panel_discovery": TextArea(
        (690, 340, 968, 396), FONT_CONDENSED, 19, 13,
        (145, 238, 255, 255), align="center", padding=3,
    ),
    "panel_scans": TextArea(
        (690, 413, 968, 469), FONT_CONDENSED, 18, 12,
        (145, 238, 255, 255), align="center", padding=3,
    ),
    "panel_coffee": TextArea(
        (690, 486, 968, 542), FONT_CONDENSED, 18, 12,
        (145, 238, 255, 255), align="center", padding=3,
    ),
    "mug_commander": TextArea(
        (348, 641, 448, 722), FONT_CONDENSED_BOLD, 15, 10,
        (35, 22, 12, 255), align="center", spacing=1, padding=4,
        stroke_width=1, stroke_fill=(245, 222, 174, 255),
    ),
    "mug_helper": TextArea(
        (1264, 639, 1368, 720), FONT_CONDENSED_BOLD, 16, 10,
        (35, 22, 12, 255), align="center", spacing=1, padding=4,
        stroke_width=1, stroke_fill=(245, 222, 174, 255),
    ),
    "todo": TextArea(
        (72, 769, 300, 945), FONT_CONDENSED_BOLD, 14, 12,
        (57, 39, 19, 255), align="left", spacing=4, padding=13,
    ),
    "expedition": TextArea(
        (397, 750, 716, 949), FONT_CONDENSED, 18, 12,
        (52, 39, 25, 255), align="left", spacing=4, padding=13,
    ),
    "sticky_note": TextArea(
        (793, 833, 1010, 934), FONT_CONDENSED_BOLD, 22, 14,
        (62, 42, 18, 255), align="center", padding=9,
    ),
    "tablet": TextArea(
        (750, 710, 970, 767), FONT_CONDENSED_BOLD, 14, 11,
        (230, 240, 236, 255), align="center", padding=5,
    ),
    "footer": TextArea(
        (252, 978, 1284, 1018), FONT_CONDENSED, 21, 14,
        (235, 242, 245, 255), align="center", padding=5,
        background=(3, 13, 20, 220), outline=(28, 117, 151, 230),
        radius=12,
    ),
}

PANEL_KEYS = {
    "panel_jump", "panel_bio", "panel_discovery", "panel_scans", "panel_coffee"
}

STICKY_NOTE_Y_OFFSET = -20


def language_paths(language: str, final: bool = False) -> tuple[Path, Path]:
    if re.fullmatch(r"[a-z]{2}", language) is None:
        raise ValueError("Die Sprache muss aus genau zwei Kleinbuchstaben bestehen")
    text_source = TEXT_DIR / f"cmdrhelper_intro_{language}.py"
    if not text_source.is_file():
        raise FileNotFoundError(f"Keine Textdatei für Sprache {language!r}: {text_source}")
    suffix = "" if final else "_test"
    output = OUTPUT_DIR / f"cmdrhelper_readme_{language}{suffix}.png"
    return text_source, output


def load_texts(text_source: Path) -> dict[str, str]:
    spec = importlib.util.spec_from_file_location(
        f"cmdrhelper_intro_{text_source.stem.rsplit('_', 1)[-1]}", text_source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Textdatei kann nicht geladen werden: {text_source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    texts = getattr(module, "TEXTS", None)
    if not isinstance(texts, dict) or set(texts) != set(AREAS):
        raise ValueError("TEXTS muss exakt die 15 erwarteten Schlüssel enthalten")
    if not all(isinstance(value, str) for value in texts.values()):
        raise TypeError("Alle TEXTS-Werte müssen Zeichenketten sein")
    return texts


def wrap_paragraph(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
                   width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines = [words[0]]
    for word in words[1:]:
        candidate = f"{lines[-1]} {word}"
        if draw.textlength(candidate, font=font) <= width:
            lines[-1] = candidate
        else:
            lines.append(word)
    return lines


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
              width: int) -> str:
    lines: list[str] = []
    for explicit_line in text.split("\n"):
        lines.extend(wrap_paragraph(draw, explicit_line, font, width))
    return "\n".join(lines)


def fit_text(draw: ImageDraw.ImageDraw, text: str, area: TextArea
             ) -> tuple[ImageFont.FreeTypeFont, str, int]:
    x1, y1, x2, y2 = area.box
    width = x2 - x1 - 2 * area.padding
    height = y2 - y1 - 2 * area.padding
    for size in range(area.max_size, area.min_size - 1, -1):
        font = ImageFont.truetype(str(area.font), size)
        wrapped = wrap_text(draw, text, font, width)
        bbox = draw.multiline_textbbox(
            (0, 0), wrapped, font=font, spacing=area.spacing, align=area.align
        )
        if bbox[2] - bbox[0] <= width and bbox[3] - bbox[1] <= height:
            return font, wrapped, size
    raise ValueError(f"Text passt nicht in Bereich {area.box}: {text!r}")


def fit_sticky_note(draw: ImageDraw.ImageDraw, text: str, area: TextArea
                    ) -> tuple[ImageFont.FreeTypeFont, str, int, int]:
    """Fit text to the note's tapered safe area without changing other regions."""
    x1, y1, x2, y2 = area.box
    safe_widths = (190, 150)
    safe_height = 62
    explicit_lines = text.split("\n")
    for size in range(area.max_size, area.min_size - 1, -1):
        font = ImageFont.truetype(str(area.font), size)
        if len(explicit_lines) != len(safe_widths):
            continue
        widths = [draw.textlength(line, font=font) for line in explicit_lines]
        if any(width > limit for width, limit in zip(widths, safe_widths)):
            continue
        wrapped = "\n".join(explicit_lines)
        for spacing in range(area.spacing, 0, -1):
            bbox = draw.multiline_textbbox(
                (0, 0), wrapped, font=font, spacing=spacing, align=area.align
            )
            if bbox[3] - bbox[1] <= safe_height and bbox[2] - bbox[0] <= x2 - x1:
                return font, wrapped, size, spacing
    raise ValueError(f"Sticky-Note-Text passt nicht sicher auf den Zettel: {text!r}")


def render(language: str, final: bool = False) -> tuple[Path, list[tuple[str, str, int]]]:
    text_source, output = language_paths(language, final=final)
    if output.exists():
        raise FileExistsError(f"Ausgabedatei existiert bereits: {output}")
    texts = load_texts(text_source)
    with Image.open(MASTER) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    used: list[tuple[str, str, int]] = []
    check_font = ImageFont.truetype(str(FONT_BOLD), 22)

    for key, area in AREAS.items():
        x1, y1, x2, y2 = area.box
        if area.background is not None:
            draw.rounded_rectangle(
                area.box, radius=area.radius, fill=area.background,
                outline=area.outline, width=2 if area.outline else 1,
            )
        if key in PANEL_KEYS:
            check_bbox = draw.textbbox((0, 0), "✓", font=check_font)
            check_height = check_bbox[3] - check_bbox[1]
            draw.text(
                (663, y1 + (y2 - y1 - check_height) / 2 - check_bbox[1]),
                "✓", font=check_font, fill=(92, 230, 126, 255),
            )
        if key == "sticky_note":
            font, wrapped, size, text_spacing = fit_sticky_note(draw, texts[key], area)
        else:
            font, wrapped, size = fit_text(draw, texts[key], area)
            text_spacing = area.spacing
        bbox = draw.multiline_textbbox(
            (0, 0), wrapped, font=font, spacing=text_spacing, align=area.align
        )
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if area.align == "left":
            tx = x1 + area.padding
        elif area.align == "right":
            tx = x2 - area.padding - text_width
        else:
            tx = x1 + (x2 - x1 - text_width) / 2
        ty = y1 + (y2 - y1 - text_height) / 2 - bbox[1]
        if key == "sticky_note":
            ty += STICKY_NOTE_Y_OFFSET
        draw.multiline_text(
            (tx, ty), wrapped, font=font, fill=area.fill,
            spacing=text_spacing, align=area.align,
            stroke_width=area.stroke_width, stroke_fill=area.stroke_fill,
        )
        used.append((key, area.font.name, size))

    image.convert("RGB").save(output, format="PNG", optimize=True)
    return output, used


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", help="Sprachcode, z. B. de oder en")
    parser.add_argument(
        "--final", action="store_true", help="Finalen Dateinamen ohne _test verwenden"
    )
    args = parser.parse_args()
    output, used = render(args.language, final=args.final)
    print(f"Erzeugt: {output}")
    for key, font_name, size in used:
        print(f"{key}: {font_name}, {size} px")


if __name__ == "__main__":
    main()
