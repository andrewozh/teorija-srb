#!/usr/bin/env python3
"""
Extract correct answers from "SVA-PITANJA-sa-resenjima.pdf".

The PDF marks correct answers with red circles (vector ellipses) drawn
around the option letter (а, б, в, г, д). This script:

1. For each section defined in sections.json, finds its page range
2. Detects red circle paths on each page
3. Matches each circle to the nearest option letter by coordinate proximity
4. Merges the results into questions.json
"""

import re
import json
import fitz  # PyMuPDF
from pathlib import Path

BASE_DIR = Path(__file__).parent
ANSWERS_PDF = BASE_DIR / "source_17042026" / "SVA-PITANJA-sa-resenjima.pdf"
QUESTIONS_JSON = BASE_DIR / "questions.json"
SECTIONS_FILE = BASE_DIR / "sections.json"

MAX_CIRCLE_SIZE = 20
MAX_MATCH_DISTANCE = 20

# All known section headers (used to detect section boundaries)
ALL_SECTION_HEADERS = [
    "ОСНОВЕ БЕЗБЕДНОСТИ САОБРАЋАЈА И ПОЈМОВИ",
    "ПРАВИЛА САОБРАЋАЈА",
    "САОБРАЋАЈНА СИГНАЛИЗАЦИЈА",
    "ВОЗАЧИ",
    "ВОЗИЛА",
    "ПОСЕБНЕ МЕРЕ И ОВЛАШЋЕЊА",
    "ПОСЛЕДИЦЕ НЕПОШТОВАЊА ПРОПИСА",
]


def find_section_pages(doc: fitz.Document, header: str) -> tuple[int, int] | None:
    """Find page range for a section (0-indexed, exclusive end).

    Returns None if the section is not found.
    """
    start = None
    for pn in range(doc.page_count):
        text = doc[pn].get_text()[:800]
        if header not in text:
            continue
        # Real section has standalone question numbers, not errata references
        if re.search(r"^1\.\s*$", text, re.MULTILINE):
            start = pn
            break

    if start is None:
        return None

    # Find end: next section header on a different page
    other_headers = [h for h in ALL_SECTION_HEADERS if h != header]
    end = doc.page_count
    for pn in range(start + 1, doc.page_count):
        text = doc[pn].get_text()[:800]
        if any(h in text for h in other_headers):
            if re.search(r"^1\.\s*$", text, re.MULTILINE):
                end = pn
                break

    return start, end


def find_circles(page: fitz.Page) -> list[fitz.Rect]:
    circles = []
    for path in page.get_drawings():
        has_curves = any(item[0] in ("c", "qu") for item in path["items"])
        if not has_curves:
            continue
        rect = path["rect"]
        if rect.width < MAX_CIRCLE_SIZE and rect.height < MAX_CIRCLE_SIZE:
            circles.append(rect)
    return circles


def find_option_positions(page: fitz.Page) -> list[tuple[float, float, str, int | None]]:
    blocks = page.get_text("dict")["blocks"]
    current_qnum = None
    positions = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            line_text = "".join(s["text"] for s in line["spans"]).strip()

            m = re.match(r"^(\d{1,3})\.?\s*$", line_text)
            if m:
                current_qnum = int(m.group(1))
                continue
            m = re.match(r"^(\d{1,3})\.?\s+\S", line_text)
            if m:
                current_qnum = int(m.group(1))

            for span in line["spans"]:
                st = span["text"].strip()
                if re.match(r"^[а-е]\)$", st):
                    x, y = span["origin"]
                    positions.append((x, y, st[0], current_qnum))

    return positions


def extract_section_answers(doc: fitz.Document, start: int, end: int) -> dict[int, list[str]]:
    """Extract answers for a page range."""
    all_answers = {}
    total_circles = 0

    for pn in range(start, end):
        page = doc[pn]
        circles = find_circles(page)
        if not circles:
            continue
        total_circles += len(circles)

        options = find_option_positions(page)
        for circle in circles:
            cx = (circle.x0 + circle.x1) / 2
            cy = (circle.y0 + circle.y1) / 2

            best_dist = MAX_MATCH_DISTANCE
            best_match = None
            for ox, oy, letter, qnum in options:
                dist = ((cx - ox) ** 2 + (cy - oy) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_match = (qnum, letter)

            if best_match and best_match[0]:
                qnum, letter = best_match
                all_answers.setdefault(qnum, []).append(letter)

    for qnum in all_answers:
        all_answers[qnum] = sorted(set(all_answers[qnum]))

    return all_answers


def main():
    sections = json.loads(SECTIONS_FILE.read_text(encoding="utf-8"))
    data = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))

    print(f"Opening {ANSWERS_PDF.name}...")
    doc = fitz.open(str(ANSWERS_PDF))
    print(f"  {doc.page_count} pages")

    # Build section_id -> question indices map
    q_by_section = {}
    for i, q in enumerate(data["questions"]):
        q_by_section.setdefault(q["section"], []).append(i)

    total_new = 0
    total_updated = 0

    for sec in sections:
        if not sec.get("answers_header"):
            continue
        if sec["id"] not in q_by_section:
            continue

        pages = find_section_pages(doc, sec["answers_header"])
        if pages is None:
            print(f"\n  ⚠️  Section '{sec['name']}' not found in answers PDF")
            continue

        start, end = pages
        print(f"\n  {sec['name']}: pages {start+1}–{end}")

        answers = extract_section_answers(doc, start, end)
        print(f"    Questions with answers: {len(answers)}")

        # Merge into questions
        new_count = 0
        updated_count = 0
        for idx in q_by_section[sec["id"]]:
            q = data["questions"][idx]
            qid = q["id"]
            if qid not in answers:
                continue
            if q.get("is_verified"):
                continue
            correct = answers[qid]

            if "correct_answers" not in q:
                q["correct_answers"] = correct
                new_count += 1
            elif q["correct_answers"] != correct:
                q["correct_answers"] = correct
                updated_count += 1

        print(f"    New: {new_count}, Updated: {updated_count}")
        total_new += new_count
        total_updated += updated_count

    doc.close()

    # Update metadata
    with_ans = sum(1 for q in data["questions"] if "correct_answers" in q)
    total = len(data["questions"])
    removed = sum(1 for q in data["questions"] if q.get("is_removed"))

    data["metadata"]["answers_coverage"] = f"{with_ans}/{total}"
    data["metadata"]["answers_source"] = (
        "Red circles in SVA-PITANJA-sa-resenjima.pdf (vector path detection)"
    )
    data["metadata"]["removed_questions"] = removed

    QUESTIONS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Consistency
    active = [q for q in data["questions"] if not q.get("is_removed")]
    mismatches = sum(
        1 for q in active
        if "correct_answers" in q
        and q["correct_answers_count"] != len(q["correct_answers"])
    )
    invalid = sum(
        1 for q in active
        if "correct_answers" in q
        and any(c not in {o["letter"] for o in q["options"]} for c in q["correct_answers"])
    )

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_new} new, {total_updated} updated")
    print(f"Coverage: {with_ans}/{total}")
    print(f"Count mismatches: {mismatches}")
    print(f"Invalid letters: {invalid}")


if __name__ == "__main__":
    main()
