#!/usr/bin/env python3
"""
Parser v3: Serbian driving exam PDF → structured JSON.

Features:
- Two-column layout handling via PyMuPDF coordinate-based extraction
- Overlapping question-number block merging
- Inline multi-option line splitting
- Image extraction and coordinate-based linking to questions
"""

import re
import json
import fitz  # PyMuPDF
from pathlib import Path

PDF_PATH = Path(__file__).parent / "pdf" / "Pravila saobracaja PDF.pdf"
OUTPUT_FILE = Path(__file__).parent / "questions.json"
IMAGES_DIR = Path(__file__).parent / "images"

MULTI_ANSWER_RE = re.compile(
    r"\(Заокружити\s+(два|три|четири)\s+тачна?\s+одговора?\)", re.IGNORECASE
)
MULTI_COUNT = {"два": 2, "три": 3, "четири": 4}

HAS_IMAGE_RE = re.compile(r"(приказан|на\s+слиц)")
CATEGORY_LABELS = {"A", "AM", "B", "BE", "C", "CE", "D", "DE", "F"}
OPTION_RE = re.compile(r"^([а-дА-Д])\)\s*(.*)")
QNUM_RE = re.compile(r"^(\d{1,4})\.\s*(.*)", re.DOTALL)
QNUM_STANDALONE_RE = re.compile(r"^(\d{1,4})\.\s*$")

NOISE_PATTERNS = [
    "Забрањено је коришћење",
    "којим средствима",
    "комерцијалне сврхе",
    "РЕПУБЛИКА СРБИЈА",
    "МИНИСТАРСТВО УНУТРАШЊИХ",
    "УПРАВА САОБРАЋАЈНЕ ПОЛИЦИЈЕ",
    "ПРАВИЛА САОБРАЋАЈА",
]


def is_noise(text: str) -> bool:
    for p in NOISE_PATTERNS:
        if p in text:
            return True
    return text.strip().startswith("©")


def blocks_overlap_vertically(b1, b2):
    """Check if two blocks overlap vertically (y-axis)."""
    return b1[1] < b2[3] and b2[1] < b1[3]


def merge_qnum_blocks(blocks: list) -> list:
    """
    Merge standalone question-number blocks ("14.") into their
    overlapping parent text blocks.
    """
    qnum_blocks = []
    text_blocks = []

    for i, b in enumerate(blocks):
        text = b[4].strip()
        m = QNUM_STANDALONE_RE.match(text)
        if m and 1 <= int(m.group(1)) <= 900:
            qnum_blocks.append((i, int(m.group(1)), b))
        else:
            text_blocks.append((i, b))

    if not qnum_blocks:
        return blocks

    merged_indices = set()
    patches = {}

    for qi, qnum, qb in qnum_blocks:
        best_parent = None
        best_overlap = 0
        for ti, tb in text_blocks:
            if ti != qi and blocks_overlap_vertically(qb, tb):
                overlap = min(qb[3], tb[3]) - max(qb[1], tb[1])
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_parent = ti
        if best_parent is not None:
            merged_indices.add(qi)
            patches[best_parent] = qnum

    result = []
    for i, b in enumerate(blocks):
        if i in merged_indices:
            continue
        if i in patches:
            qnum = patches[i]
            new_text = f"{qnum}. {b[4].strip()}\n"
            result.append((b[0], b[1], b[2], b[3], new_text, b[5]))
        else:
            result.append(b)

    return result


def extract_column_blocks(page, x0, x1):
    """Extract, filter, and pre-process text blocks from a page column."""
    rect = fitz.Rect(x0, 0, x1, page.rect.height)
    blocks = page.get_text("blocks", clip=rect)
    blocks.sort(key=lambda b: (b[1], b[0]))

    filtered = []
    for block in blocks:
        text = block[4].strip()
        if not text or is_noise(text):
            continue
        if re.match(r"^\d{1,2}$", text) and int(text) < 100:
            if block[1] > page.rect.height * 0.9:
                continue
        filtered.append(block)

    return merge_qnum_blocks(filtered)


def extract_page_images(page, page_num, x_mid):
    """Extract content images from a page, save to disk, return metadata.
    
    One image xref can appear at multiple positions on the page (reused for
    similar questions). We save the file once but create a metadata entry
    for each placement so image→question linking works correctly.
    """
    images = []
    saved_xrefs = {}  # xref -> saved filename (avoid re-encoding the same pixels)

    for img_info in page.get_images(full=True):
        xref = img_info[0]
        rects = page.get_image_rects(xref)
        if not rects:
            continue

        for rect in rects:
            if rect.width < 50 or rect.height < 50:
                continue

            column = "left" if rect.x0 < x_mid else "right"
            img_filename = f"p{page_num:03d}_y{int(rect.y0):04d}.png"

            # Save pixel data once per xref, copy for additional placements
            if xref not in saved_xrefs:
                try:
                    pix = fitz.Pixmap(page.parent, xref)
                    if pix.n >= 5:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                    pix.save(str(IMAGES_DIR / img_filename))
                    saved_xrefs[xref] = img_filename
                except Exception:
                    continue
            else:
                # Same image at a different position — symlink or copy
                src = IMAGES_DIR / saved_xrefs[xref]
                dst = IMAGES_DIR / img_filename
                if not dst.exists() and src.exists():
                    import shutil
                    shutil.copy2(src, dst)

            images.append({
                "filename": img_filename,
                "page": page_num,
                "column": column,
                "y": rect.y0,
            })

    return images


# ---------------------------------------------------------------------------
# Question-level parsing
# ---------------------------------------------------------------------------

def expand_inline_options(lines: list[str]) -> list[str]:
    """Split lines with multiple options into separate lines."""
    result = []
    for line in lines:
        stripped = line.strip()

        cat_prefix = None
        for cat in sorted(CATEGORY_LABELS, key=len, reverse=True):
            if stripped.startswith(cat + " ") or stripped.startswith(cat + "\t"):
                cat_prefix = cat
                stripped = stripped[len(cat):].strip()
                break

        option_starts = list(re.finditer(r"[а-д]\)\s", stripped))

        if len(option_starts) > 1:
            if cat_prefix:
                result.append(cat_prefix)
            for i, m in enumerate(option_starts):
                start = m.start()
                end = option_starts[i + 1].start() if i + 1 < len(option_starts) else len(stripped)
                result.append(stripped[start:end].strip().rstrip(","))
        else:
            if cat_prefix:
                result.append(cat_prefix)
                if stripped:
                    result.append(stripped)
            else:
                result.append(line.strip())

    return result


def parse_column_text(text: str, page: int, column: str) -> list[dict]:
    """Parse question text from a single column, tagging with position info."""
    lines = text.split("\n")
    segments = []
    current_qnum = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines:
                current_lines.append("")
            continue

        m = re.match(r"^(\d{1,4})\.\s+(.*)", stripped)
        if m and 1 <= int(m.group(1)) <= 900:
            if current_qnum is not None:
                segments.append((current_qnum, "\n".join(current_lines)))
            current_qnum = int(m.group(1))
            rest = m.group(2).strip()
            current_lines = [rest] if rest else []
            continue

        m2 = QNUM_STANDALONE_RE.match(stripped)
        if m2 and 1 <= int(m2.group(1)) <= 900:
            if current_qnum is not None:
                segments.append((current_qnum, "\n".join(current_lines)))
            current_qnum = int(m2.group(1))
            current_lines = []
            continue

        if current_qnum is not None:
            current_lines.append(stripped)

    if current_qnum is not None:
        segments.append((current_qnum, "\n".join(current_lines)))

    questions = []
    for qnum, block_text in segments:
        q = parse_single_question(qnum, block_text)
        q["_page"] = page
        q["_column"] = column
        questions.append(q)

    return questions


def parse_single_question(qnum: int, block_text: str) -> dict:
    """Parse a single question's text block into structured data."""
    lines = expand_inline_options(block_text.split("\n"))

    categories = []
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped in CATEGORY_LABELS:
            categories.append(stripped)
        else:
            cleaned_lines.append(stripped)

    option_entries = []
    for i, line in enumerate(cleaned_lines):
        m = OPTION_RE.match(line.strip())
        if m:
            option_entries.append((i, m.group(1).lower(), m.group(2).strip()))

    first_opt_idx = option_entries[0][0] if option_entries else len(cleaned_lines)
    q_text_parts = [s.strip() for s in cleaned_lines[:first_opt_idx] if s.strip() and s.strip() not in ("2", "3")]
    q_text = " ".join(q_text_parts)

    multi_match = MULTI_ANSWER_RE.search(block_text)
    correct_count = MULTI_COUNT.get(multi_match.group(1), 1) if multi_match else 1

    q_text = re.sub(r"\s+", " ", MULTI_ANSWER_RE.sub("", q_text)).strip()

    options = []
    for oi, (opt_idx, letter, opt_text) in enumerate(option_entries):
        next_opt_idx = option_entries[oi + 1][0] if oi + 1 < len(option_entries) else len(cleaned_lines)
        parts = [opt_text]
        for ci in range(opt_idx + 1, next_opt_idx):
            cl = cleaned_lines[ci].strip()
            if cl in ("2", "3", "") or cl in CATEGORY_LABELS or OPTION_RE.match(cl):
                break
            parts.append(cl)
        full_text = re.sub(r"\s+[23]$", "", " ".join(parts))
        full_text = re.sub(r"\s+", " ", full_text).strip().rstrip(",").rstrip(".")
        options.append({"letter": letter, "text": full_text})

    points = 2
    for line in reversed(cleaned_lines):
        s = line.strip()
        if s in ("2", "3"):
            points = int(s)
            break
        m = re.search(r"\s([23])$", s)
        if m:
            points = int(m.group(1))
            break

    has_image = bool(HAS_IMAGE_RE.search(q_text))

    result = {
        "id": qnum,
        "text": q_text,
        "options": options,
        "points": points,
        "correct_answers_count": correct_count,
        "has_image": has_image,
    }
    if categories:
        result["categories"] = sorted(set(categories))

    return result


# ---------------------------------------------------------------------------
# Question status flags (removed / changed / new)
# ---------------------------------------------------------------------------

def extract_question_flags(doc: fitz.Document, x_mid: float) -> dict[int, dict]:
    """Detect question status from colored background highlights in the PDF.

    The official MUP PDF uses colored backgrounds:
    - RED:    removed from exam database  → is_removed
    - YELLOW: modified question            → is_changed
    - GREEN:  new question                 → is_new
    """
    flags = {}

    for pn in range(doc.page_count):
        page = doc[pn]

        # Collect colored rectangular fills (skip answer-marker circles)
        colored_rects = []
        for p in page.get_drawings():
            fill = p.get("fill")
            if not fill or fill == (0, 0, 0):
                continue
            if any(item[0] in ("c", "qu") for item in p["items"]):
                continue
            r = p["rect"]
            if r.width > 20 and r.height > 5:
                colored_rects.append((r, fill))

        if not colored_rects:
            continue

        # Find question number positions on this page
        blocks = page.get_text("dict")["blocks"]
        q_positions = []  # (qnum, y_top, y_bottom, x)
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = "".join(s["text"] for s in line["spans"]).strip()
                m = re.match(r"^(\d{1,3})\.\s*$", line_text)
                if not m:
                    m = re.match(r"^(\d{1,3})\.\s+\S", line_text)
                if m:
                    qnum = int(m.group(1))
                    bbox = line["bbox"]
                    q_positions.append((qnum, bbox[1], bbox[3], bbox[0]))

        # Match questions to colored rects (same column + vertical overlap)
        for i, (qnum, qy_top, qy_bot, qx) in enumerate(q_positions):
            qy_extent = (
                q_positions[i + 1][1]
                if i + 1 < len(q_positions)
                else page.rect.height
            )
            q_is_right = qx > x_mid

            for rect, fill in colored_rects:
                if (rect.x0 > x_mid) != q_is_right:
                    continue
                if rect.y0 < qy_extent and rect.y1 > qy_top:
                    r, g, b = fill
                    if r > 0.8 and g < 0.3 and b < 0.3:
                        flags.setdefault(qnum, {})["is_removed"] = True
                    elif g > 0.5 and r < 0.3:
                        flags.setdefault(qnum, {})["is_new"] = True
                    elif r > 0.8 and g > 0.8 and b < 0.3:
                        flags.setdefault(qnum, {})["is_changed"] = True
                    break

    return flags


# ---------------------------------------------------------------------------
# Image ↔ Question linking
# ---------------------------------------------------------------------------

def link_images_to_questions(questions: list[dict], all_images: list[dict]) -> None:
    """
    Match images to questions by page + column + y-position proximity.

    In the PDF, images sit between the question text and the answer options,
    so the closest image below a question's y-start (on the same page/column)
    belongs to that question.
    """
    # Group images by (page, column)
    img_index = {}
    for img in all_images:
        key = (img["page"], img["column"])
        img_index.setdefault(key, []).append(img)
    for v in img_index.values():
        v.sort(key=lambda i: i["y"])

    # Group questions by (page, column), preserving order (by id)
    q_index = {}
    for q in questions:
        key = (q.get("_page"), q.get("_column"))
        q_index.setdefault(key, []).append(q)

    linked = 0
    for key, page_images in img_index.items():
        page_questions = q_index.get(key, [])
        # Only consider questions that reference an image
        img_questions = [q for q in page_questions if q["has_image"]]

        if not img_questions:
            continue

        # Match sequentially: images and image-questions appear in the same
        # top-to-bottom order within a page/column
        for i, q in enumerate(img_questions):
            if i < len(page_images):
                q["image"] = page_images[i]["filename"]
                linked += 1

    print(f"  Images linked to questions: {linked}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Opening {PDF_PATH}...")
    doc = fitz.open(str(PDF_PATH))
    print(f"  {doc.page_count} pages")

    page_width = doc[0].rect.width
    x_mid = page_width / 2
    print(f"  Page width: {page_width:.0f}pt, column split at {x_mid:.0f}pt")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    all_questions = []
    all_images = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        pn = page_num + 1  # 1-based

        left_blocks = extract_column_blocks(page, 0, x_mid - 5)
        right_blocks = extract_column_blocks(page, x_mid - 5, page_width)

        left_text = "\n".join(b[4].strip() for b in left_blocks if b[4].strip())
        right_text = "\n".join(b[4].strip() for b in right_blocks if b[4].strip())

        all_questions.extend(parse_column_text(left_text, pn, "left"))
        all_questions.extend(parse_column_text(right_text, pn, "right"))

        all_images.extend(extract_page_images(page, pn, x_mid))

    doc.close()

    print(f"\n  Raw questions: {len(all_questions)}")
    print(f"  Images extracted: {len(all_images)}")

    # Deduplicate
    seen = {}
    for q in all_questions:
        qid = q["id"]
        if qid not in seen or (len(q["options"]) * 10 + len(q["text"])) > (len(seen[qid]["options"]) * 10 + len(seen[qid]["text"])):
            seen[qid] = q
    questions = sorted(seen.values(), key=lambda q: q["id"])
    print(f"  After dedup: {len(questions)}")

    # Link images
    link_images_to_questions(questions, all_images)

    # Extract question status flags (removed/changed/new)
    doc = fitz.open(str(PDF_PATH))
    q_flags = extract_question_flags(doc, x_mid)
    doc.close()

    removed = sum(1 for f in q_flags.values() if f.get("is_removed"))
    changed = sum(1 for f in q_flags.values() if f.get("is_changed"))
    new = sum(1 for f in q_flags.values() if f.get("is_new"))
    print(f"  Flags: {removed} removed, {changed} changed, {new} new")

    for q in questions:
        if q["id"] in q_flags:
            for flag, value in q_flags[q["id"]].items():
                q[flag] = value

    # Clean internal position tags
    for q in questions:
        q.pop("_page", None)
        q.pop("_column", None)

    # Stats
    good = sum(1 for q in questions if len(q["options"]) >= 2 and len(q["text"]) > 10)
    no_opts = sum(1 for q in questions if len(q["options"]) == 0)
    with_images = sum(1 for q in questions if q["has_image"])
    linked_images = sum(1 for q in questions if "image" in q)
    multi = sum(1 for q in questions if q["correct_answers_count"] > 1)
    cats = sum(1 for q in questions if "categories" in q)
    pts = {}
    for q in questions:
        pts[q["points"]] = pts.get(q["points"], 0) + 1

    ids = [q["id"] for q in questions]
    missing = sorted(set(range(1, max(ids) + 1)) - set(ids)) if ids else []

    print(f"\nResults:")
    print(f"  ✅ Good (>=2 opts, text>10):  {good}")
    print(f"  ❌ No options:                {no_opts}")
    print(f"  📷 With images:               {with_images}")
    print(f"  🔗 Images linked:             {linked_images}")
    print(f"  ✏️  Multi-answer:              {multi}")
    print(f"  🏷️  With categories:           {cats}")
    print(f"  Points: {pts}")
    print(f"  Missing IDs: {len(missing)}")

    # Save
    output = {
        "metadata": {
            "source": "МУП Србије — Управа саобраћајне полиције",
            "section": "Правила саобраћаја",
            "total_questions": len(questions),
            "questions_with_images": with_images,
            "images_linked": linked_images,
            "note": "Correct answers NOT included.",
        },
        "questions": questions,
    }

    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {OUTPUT_FILE}")

    # Samples
    print("\n=== QUESTION WITH IMAGE ===")
    qi = next((q for q in questions if "image" in q), None)
    if qi:
        print(json.dumps(qi, ensure_ascii=False, indent=2))

    print("\n=== QUESTION WITHOUT IMAGE ===")
    qn = next((q for q in questions if not q["has_image"] and len(q["options"]) >= 3), None)
    if qn:
        print(json.dumps(qn, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
