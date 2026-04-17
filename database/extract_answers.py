#!/usr/bin/env python3
"""
Extract correct answers from "SVA-PITANJA-sa-resenjima.pdf".

The PDF marks correct answers with red circles (vector ellipses) drawn
around the option letter (а, б, в, г, д). This script:

1. Finds the "ПРАВИЛА САОБРАЋАЈА" section in the PDF
2. Detects red circle paths on each page (small curved vector drawings)
3. Matches each circle to the nearest option letter by coordinate proximity
4. Merges the results into questions.json
"""

import re
import json
import fitz  # PyMuPDF
from pathlib import Path

ANSWERS_PDF = Path(__file__).parent / "pdf" / "SVA-PITANJA-sa-resenjima.pdf"
QUESTIONS_JSON = Path(__file__).parent / "questions.json"

# Section to extract (change for other exam sections)
SECTION_HEADER = "ПРАВИЛА САОБРАЋАЈА"
SECTION_END_MARKERS = ["ПОСЕБНЕ МЕРЕ", "ПОСЛЕДИЦЕ НЕПОШТОВАЊА"]

MAX_CIRCLE_SIZE = 20  # px — circles around letters are ~12x11
MAX_MATCH_DISTANCE = 20  # pt — max distance from circle center to option letter


def find_section_pages(doc: fitz.Document) -> tuple[int, int]:
    """Find page range for the target section (0-indexed, exclusive end).

    Distinguishes the actual question pages from errata/amendment pages
    that also mention the section header. The real section has "1." as
    the first question, not "Питање број NNN."
    """
    start = None
    for pn in range(doc.page_count):
        text = doc[pn].get_text()[:500]
        if SECTION_HEADER not in text:
            continue
        # The real section has standalone question numbers ("1.\n", "2.\n")
        # not inline references like "1. Закона" in errata text
        if re.search(r"^1\.\s*$", text, re.MULTILINE):
            start = pn
            break

    if start is None:
        raise ValueError(f"Section '{SECTION_HEADER}' not found in PDF")

    end = doc.page_count
    for pn in range(start + 1, doc.page_count):
        text = doc[pn].get_text()[:500]
        if any(marker in text for marker in SECTION_END_MARKERS):
            end = pn
            break

    return start, end


def find_circles(page: fitz.Page) -> list[fitz.Rect]:
    """Find small red circle/ellipse vector paths on a page."""
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
    """Find option letter positions (x, y, letter, question_number) on a page."""
    blocks = page.get_text("dict")["blocks"]
    current_qnum = None
    positions = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            line_text = "".join(s["text"] for s in line["spans"]).strip()

            # Detect question number
            m = re.match(r"^(\d{1,3})\.\s*$", line_text)
            if m:
                current_qnum = int(m.group(1))
                continue
            m = re.match(r"^(\d{1,3})\.\s+\S", line_text)
            if m:
                current_qnum = int(m.group(1))

            # Detect option letters: "а)", "б)", etc.
            for span in line["spans"]:
                st = span["text"].strip()
                if re.match(r"^[а-д]\)$", st):
                    x, y = span["origin"]
                    positions.append((x, y, st[0], current_qnum))

    return positions


def match_circles_to_options(
    circles: list[fitz.Rect],
    options: list[tuple[float, float, str, int | None]],
) -> dict[int, list[str]]:
    """Match each circle to the nearest option letter. Returns {qnum: [letters]}."""
    answers = {}

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
            answers.setdefault(qnum, []).append(letter)

    # Deduplicate and sort
    for qnum in answers:
        answers[qnum] = sorted(set(answers[qnum]))

    return answers


def extract_answers() -> dict[int, list[str]]:
    """Extract correct answers and question status flags from the PDF."""
    print(f"Opening {ANSWERS_PDF}...")
    doc = fitz.open(str(ANSWERS_PDF))
    print(f"  {doc.page_count} pages")

    start, end = find_section_pages(doc)
    print(f"  Section '{SECTION_HEADER}': pages {start + 1}–{end}")

    # Extract answers from red circles
    all_answers = {}
    total_circles = 0

    for pn in range(start, end):
        page = doc[pn]
        circles = find_circles(page)
        if not circles:
            continue
        total_circles += len(circles)

        options = find_option_positions(page)
        page_answers = match_circles_to_options(circles, options)
        for qnum, letters in page_answers.items():
            all_answers.setdefault(qnum, []).extend(letters)

    # Deduplicate
    for qnum in all_answers:
        all_answers[qnum] = sorted(set(all_answers[qnum]))

    print(f"  Circles found: {total_circles}")
    print(f"  Questions with answers: {len(all_answers)}")

    doc.close()

    return all_answers


def merge_answers(answers: dict[int, list[str]]) -> None:
    """Merge extracted answers into questions.json."""
    print(f"\nMerging into {QUESTIONS_JSON}...")
    data = json.load(QUESTIONS_JSON.open())

    new_count = 0
    updated_count = 0

    for q in data["questions"]:
        qid = q["id"]
        if qid not in answers:
            continue
        correct = answers[qid]

        # Update correct_answers_count for changed questions
        if q.get("is_changed") and len(correct) != q["correct_answers_count"]:
            q["correct_answers_count"] = len(correct)

        if "correct_answers" not in q:
            q["correct_answers"] = correct
            new_count += 1
        elif q["correct_answers"] != correct:
            q["correct_answers"] = correct
            updated_count += 1

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

    # Consistency checks (skip removed questions)
    active = [q for q in data["questions"] if not q.get("is_removed")]
    mismatches = sum(
        1
        for q in active
        if "correct_answers" in q
        and q["correct_answers_count"] != len(q["correct_answers"])
    )
    invalid = sum(
        1
        for q in active
        if "correct_answers" in q
        and any(
            c not in {o["letter"] for o in q["options"]}
            for c in q["correct_answers"]
        )
    )

    print(f"  New answers:   {new_count}")
    print(f"  Updated:       {updated_count}")
    print(f"  Coverage:      {with_ans}/{total}")
    print(f"  Count mismatches (active only): {mismatches}")
    print(f"  Invalid letters: {invalid}")


def main():
    answers = extract_answers()
    merge_answers(answers)

    # Show sample
    print("\nVerification:")
    for qid in [1, 4, 14, 18, 44, 100, 317, 400, 700]:
        print(f"  Q{qid}: {answers.get(qid, '❌ not found')}")


if __name__ == "__main__":
    main()
