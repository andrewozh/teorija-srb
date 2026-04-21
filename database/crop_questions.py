#!/usr/bin/env python3
"""
Crop individual question screenshots from SVA-PITANJA-sa-resenjima.pdf.

Uses thick horizontal bars (outer table borders, thickness >= 1.0pt) to detect
question boundaries. Each question is enclosed in a table with thick outer borders
and thin inner cell dividers — we only care about the outer ones.

Output: db_new/<section_id>/q<NNN>.png
"""

import fitz
from PIL import Image
import io
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent
PDF_PATH = BASE_DIR / "source_17042026" / "SVA-PITANJA-sa-resenjima.pdf"
OUTPUT_DIR = BASE_DIR.parent / "db_new"
DPI = 200

SECTIONS = [
    {"id": "01_osnove_bezbednosti",   "name": "Основе безбедности саобраћаја и појмови", "expected": 170, "pages": (11, 28)},
    {"id": "02_vozaci",               "name": "Возачи",                                  "expected": 216, "pages": (29, 46)},
    {"id": "03_vozila",               "name": "Возила",                                  "expected": 365, "pages": (47, 72)},
    {"id": "04_signalizacija",        "name": "Саобраћајна сигнализација",               "expected": 524, "pages": (73, 151)},
    {"id": "05_pravila_saobracaja",   "name": "Правила саобраћаја",                      "expected": 797, "pages": (152, 238)},
    {"id": "06_posebne_mere",         "name": "Посебне мере и овлашћења",                "expected":  61, "pages": (239, 244)},
    {"id": "07_posledice",            "name": "Последице непоштовања прописа",            "expected": 182, "pages": (245, 260)},
]

# Column x-ranges (consistent across all pages in this PDF)
LEFT_COL = (22, 293)
RIGHT_COL = (299, 568)


def get_column_boundaries(thick_h_bars, col_x_start, col_x_end):
    """Find y-positions of thick horizontal bars that form question outer borders."""
    y_groups = defaultdict(list)
    for r in thick_h_bars:
        y_key = round(r.y0, 0)
        y_groups[y_key].append(r)

    col_width = col_x_end - col_x_start
    boundaries = []

    for y_key in sorted(y_groups.keys()):
        all_bars = y_groups[y_key]
        col_bars = [r for r in all_bars if r.x0 >= col_x_start - 5 and r.x1 <= col_x_end + 5]
        if not col_bars:
            continue

        group_x_min = min(r.x0 for r in col_bars)
        total_w = sum(r.width for r in col_bars)

        if abs(group_x_min - col_x_start) > 5 or total_w < col_width * 0.8:
            continue

        # Exclude header/footer: a single bar that straddles the column edge
        is_header_footer = any(
            (r.x0 < col_x_end and r.x1 > col_x_end + 10) or
            (r.x1 > col_x_start and r.x0 < col_x_start - 10)
            for r in all_bars
        )
        if is_header_footer:
            continue

        boundaries.append(col_bars[0].y0)

    return boundaries


def extract_questions_from_page(page, scale, full_img):
    """Extract question crops from a single page. Returns list of PIL Images."""
    drawings = page.get_drawings()
    thick_h = [d['rect'] for d in drawings
               if d.get('fill') == (0, 0, 0)
               and d['rect'].height >= 1.0 and d['rect'].width > 15]

    questions = []

    for col_x_start, col_x_end in [LEFT_COL, RIGHT_COL]:
        boundaries = get_column_boundaries(thick_h, col_x_start, col_x_end)
        boxes = [(boundaries[i], boundaries[i + 1]) for i in range(0, len(boundaries) - 1, 2)]

        for y0, y1 in boxes:
            # y1 is the top edge of the bottom border bar (1.5pt thick).
            # Add bar thickness + small padding so the border isn't cut off.
            cropped = full_img.crop((
                int(col_x_start * scale),
                int(y0 * scale),
                int(col_x_end * scale),
                int((y1 + 2) * scale),
            ))
            questions.append(cropped)

    return questions


def process_section(doc, section):
    """Process all pages of a section, save question screenshots."""
    section_dir = OUTPUT_DIR / section["id"]
    section_dir.mkdir(parents=True, exist_ok=True)

    page_start, page_end = section["pages"]
    # Convert 1-indexed page numbers to 0-indexed
    page_start_idx = page_start - 1
    page_end_idx = page_end - 1

    q_num = 0

    for page_idx in range(page_start_idx, page_end_idx + 1):
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=DPI)
        full_img = Image.open(io.BytesIO(pix.tobytes('png')))
        scale = pix.width / page.rect.width

        crops = extract_questions_from_page(page, scale, full_img)

        for crop_img in crops:
            q_num += 1
            fname = f"q{q_num:03d}.png"
            crop_img.save(str(section_dir / fname))

    return q_num


def main():
    doc = fitz.open(str(PDF_PATH))
    print(f"PDF: {PDF_PATH.name} ({doc.page_count} pages)")
    print(f"Output: {OUTPUT_DIR}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    grand_total = 0

    for section in SECTIONS:
        count = process_section(doc, section)
        status = "✓" if count == section["expected"] else f"✗ (expected {section['expected']})"
        print(f"  {section['id']}: {count} questions {status}")
        grand_total += count

    doc.close()
    print(f"\nTotal: {grand_total} questions")


if __name__ == "__main__":
    main()
