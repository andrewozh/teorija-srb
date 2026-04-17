#!/usr/bin/env python3
"""
Parser v3: Fixed handling of overlapping question-number blocks.

Bug fixes over v2:
1. Question numbers often appear as separate small blocks overlapping the
   main text block. We now detect and merge them before parsing.
2. Some blocks contain the full question (text + options) in a single block.
   We now handle intra-block option parsing.
3. Better point-value extraction from end of lines.
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
    if text.strip().startswith("©"):
        return True
    return False


def blocks_overlap_vertically(b1, b2):
    """Check if two blocks overlap vertically (y-axis)."""
    y1_start, y1_end = b1[1], b1[3]
    y2_start, y2_end = b2[1], b2[3]
    return y1_start < y2_end and y2_start < y1_end


def merge_qnum_blocks(blocks: list) -> list:
    """
    Fix Bug #1: Merge standalone question-number blocks into their parent text blocks.
    
    PyMuPDF sometimes returns "14." as a tiny block overlapping a larger block
    that contains the actual question text + options. We detect these and merge.
    """
    # Identify standalone question number blocks
    qnum_blocks = []  # (index, qnum, block)
    text_blocks = []  # (index, block)
    
    for i, b in enumerate(blocks):
        text = b[4].strip()
        m = QNUM_STANDALONE_RE.match(text)
        if m:
            qnum = int(m.group(1))
            if 1 <= qnum <= 900:
                qnum_blocks.append((i, qnum, b))
                continue
        text_blocks.append((i, b))
    
    if not qnum_blocks:
        return blocks
    
    # For each qnum block, find a parent text block it overlaps with
    merged_indices = set()
    patches = {}  # text_block_index -> qnum to prepend
    
    for qi, qnum, qb in qnum_blocks:
        best_parent = None
        best_overlap = 0
        
        for ti, tb in text_blocks:
            if ti == qi:
                continue
            if blocks_overlap_vertically(qb, tb):
                # Calculate overlap amount
                overlap = min(qb[3], tb[3]) - max(qb[1], tb[1])
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_parent = ti
        
        if best_parent is not None:
            merged_indices.add(qi)
            patches[best_parent] = qnum
    
    # Build result: patch parent blocks and remove merged qnum blocks
    result = []
    for i, b in enumerate(blocks):
        if i in merged_indices:
            continue  # skip standalone qnum block, it's been merged
        if i in patches:
            # Prepend question number to this block's text
            qnum = patches[i]
            new_text = f"{qnum}. {b[4].strip()}\n"
            result.append((b[0], b[1], b[2], b[3], new_text, b[5]))
        else:
            result.append(b)
    
    return result


def extract_column_blocks(page, x0, x1):
    """Extract and pre-process text blocks from a column."""
    rect = fitz.Rect(x0, 0, x1, page.rect.height)
    blocks = page.get_text("blocks", clip=rect)
    blocks.sort(key=lambda b: (b[1], b[0]))
    
    # Filter noise and page numbers
    filtered = []
    for block in blocks:
        text = block[4].strip()
        if not text:
            continue
        if is_noise(text):
            continue
        # Skip page numbers at bottom of page
        if re.match(r"^\d{1,2}$", text) and int(text) < 100:
            if block[1] > page.rect.height * 0.9:
                continue
        filtered.append(block)
    
    # Merge standalone question-number blocks into parent blocks
    merged = merge_qnum_blocks(filtered)
    
    return merged


def extract_column_text(blocks: list) -> str:
    """Convert processed blocks into text."""
    lines = []
    for block in blocks:
        text = block[4].strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def extract_page_images(page, page_num, x_mid):
    """Extract images from a page."""
    images = []
    image_list = page.get_images(full=True)
    
    for img_idx, img_info in enumerate(image_list):
        xref = img_info[0]
        img_rects = page.get_image_rects(xref)
        if not img_rects:
            continue
        
        rect = img_rects[0]
        if rect.width < 50 or rect.height < 50:
            continue
        
        column = "left" if rect.x0 < x_mid else "right"
        
        try:
            pix = fitz.Pixmap(page.parent, xref)
            if pix.n >= 5:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_filename = f"p{page_num:03d}_{img_idx:02d}.png"
            img_path = IMAGES_DIR / img_filename
            pix.save(str(img_path))
            
            images.append({
                "filename": img_filename,
                "column": column,
                "y_position": rect.y0,
            })
        except Exception:
            pass
    
    return images


def parse_column_text(text: str) -> list[dict]:
    """Parse sequential question text from a single column."""
    lines = text.split("\n")
    
    # First pass: segment text by question numbers
    segments = []  # (qnum, text_block)
    current_qnum = None
    current_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines:
                current_lines.append("")
            continue
        
        # Check for "NNN. text..." (question start with text on same line)
        m = re.match(r"^(\d{1,4})\.\s+(.*)", stripped)
        if m:
            qnum = int(m.group(1))
            rest = m.group(2).strip()
            if 1 <= qnum <= 900:
                if current_qnum is not None:
                    segments.append((current_qnum, "\n".join(current_lines)))
                current_qnum = qnum
                current_lines = [rest] if rest else []
                continue
        
        # Check for standalone "NNN."
        m2 = QNUM_STANDALONE_RE.match(stripped)
        if m2:
            qnum = int(m2.group(1))
            if 1 <= qnum <= 900:
                if current_qnum is not None:
                    segments.append((current_qnum, "\n".join(current_lines)))
                current_qnum = qnum
                current_lines = []
                continue
        
        if current_qnum is not None:
            current_lines.append(stripped)
    
    if current_qnum is not None:
        segments.append((current_qnum, "\n".join(current_lines)))
    
    # Second pass: parse each segment
    questions = []
    for qnum, block_text in segments:
        question = parse_single_question(qnum, block_text)
        questions.append(question)
    
    return questions


def expand_inline_options(lines: list[str]) -> list[str]:
    """
    Split lines that contain multiple options into separate lines.
    E.g. "D а) 50 km/h, б) 70 km/h, в) 80 km/h" becomes:
      "D"
      "а) 50 km/h,"
      "б) 70 km/h,"
      "в) 80 km/h"
    Also handles "а) 50 km/h, б) 70 km/h" without category prefix.
    """
    result = []
    for line in lines:
        stripped = line.strip()
        
        # Strip leading category label if present
        cat_prefix = None
        for cat in sorted(CATEGORY_LABELS, key=len, reverse=True):
            if stripped.startswith(cat + " ") or stripped.startswith(cat + "\t"):
                cat_prefix = cat
                stripped = stripped[len(cat):].strip()
                break
        
        # Check if line has multiple options: "а) ... б) ... в) ..."
        option_starts = list(re.finditer(r"[а-д]\)\s", stripped))
        
        if len(option_starts) > 1:
            if cat_prefix:
                result.append(cat_prefix)
            for i, m in enumerate(option_starts):
                start = m.start()
                end = option_starts[i + 1].start() if i + 1 < len(option_starts) else len(stripped)
                opt_text = stripped[start:end].strip().rstrip(",")
                result.append(opt_text)
        else:
            if cat_prefix:
                result.append(cat_prefix)
                if stripped:
                    result.append(stripped)
            else:
                result.append(line.strip())
    
    return result


def parse_single_question(qnum: int, block_text: str) -> dict:
    """Parse a single question's text block into structured data."""
    raw_lines = block_text.split("\n")
    
    # Pre-process: expand inline options (multiple opts on one line)
    lines = expand_inline_options(raw_lines)
    
    # Extract categories
    categories = []
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped in CATEGORY_LABELS:
            categories.append(stripped)
        else:
            cleaned_lines.append(stripped)
    
    # Find options
    option_entries = []  # (line_idx, letter, text)
    for i, line in enumerate(cleaned_lines):
        m = OPTION_RE.match(line.strip())
        if m:
            option_entries.append((i, m.group(1).lower(), m.group(2).strip()))
    
    # Build question text (everything before first option)
    first_opt_idx = option_entries[0][0] if option_entries else len(cleaned_lines)
    q_text_parts = []
    for i in range(first_opt_idx):
        s = cleaned_lines[i].strip()
        if s and s not in ("2", "3"):
            q_text_parts.append(s)
    
    q_text = " ".join(q_text_parts)
    
    # Multi-answer detection
    multi_match = MULTI_ANSWER_RE.search(block_text)
    correct_count = MULTI_COUNT.get(multi_match.group(1), 1) if multi_match else 1
    
    q_text = MULTI_ANSWER_RE.sub("", q_text).strip()
    q_text = re.sub(r"\s+", " ", q_text).strip()
    
    # Build options with continuation lines
    options = []
    for oi, (opt_idx, letter, opt_text) in enumerate(option_entries):
        next_opt_idx = option_entries[oi + 1][0] if oi + 1 < len(option_entries) else len(cleaned_lines)
        
        parts = [opt_text]
        for ci in range(opt_idx + 1, next_opt_idx):
            cl = cleaned_lines[ci].strip()
            if cl in ("2", "3", ""):
                break
            if cl in CATEGORY_LABELS:
                break
            if OPTION_RE.match(cl):
                break
            parts.append(cl)
        
        full_text = " ".join(parts)
        full_text = re.sub(r"\s+[23]$", "", full_text)
        full_text = re.sub(r"\s+", " ", full_text).strip()
        full_text = full_text.rstrip(",").rstrip(".")
        
        options.append({"letter": letter, "text": full_text})
    
    # Points
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


def main():
    print(f"Opening {PDF_PATH}...")
    doc = fitz.open(str(PDF_PATH))
    print(f"  {doc.page_count} pages")
    
    page_width = doc[0].rect.width
    x_mid = page_width / 2
    print(f"  Page width: {page_width:.0f}pt, column split at {x_mid:.0f}pt")
    
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    all_questions = []
    total_images = 0
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Extract pre-processed blocks per column
        left_blocks = extract_column_blocks(page, 0, x_mid - 5)
        right_blocks = extract_column_blocks(page, x_mid - 5, page_width)
        
        # Convert to text and parse
        left_text = extract_column_text(left_blocks)
        right_text = extract_column_text(right_blocks)
        
        left_q = parse_column_text(left_text)
        right_q = parse_column_text(right_text)
        
        all_questions.extend(left_q)
        all_questions.extend(right_q)
        
        # Images
        images = extract_page_images(page, page_num + 1, x_mid)
        total_images += len(images)
    
    doc.close()
    
    print(f"\nRaw questions extracted: {len(all_questions)}")
    print(f"Images extracted: {total_images}")
    
    # Deduplicate — keep best version of each question
    seen = {}
    for q in all_questions:
        qid = q["id"]
        if qid in seen:
            score_new = len(q["options"]) * 10 + len(q["text"])
            score_old = len(seen[qid]["options"]) * 10 + len(seen[qid]["text"])
            if score_new > score_old:
                seen[qid] = q
        else:
            seen[qid] = q
    
    questions = sorted(seen.values(), key=lambda q: q["id"])
    print(f"After dedup: {len(questions)}")
    
    # Stats
    with_images = sum(1 for q in questions if q["has_image"])
    multi_answer = sum(1 for q in questions if q["correct_answers_count"] > 1)
    by_points = {}
    for q in questions:
        by_points[q["points"]] = by_points.get(q["points"], 0) + 1
    with_categories = sum(1 for q in questions if "categories" in q)
    no_options = sum(1 for q in questions if len(q["options"]) == 0)
    few_options = sum(1 for q in questions if 0 < len(q["options"]) < 2)
    short_text = sum(1 for q in questions if len(q["options"]) >= 2 and len(q["text"]) <= 10)
    good = sum(1 for q in questions if len(q["options"]) >= 2 and len(q["text"]) > 10)
    
    print(f"\nStats:")
    print(f"  ✅ Good (>=2 opts, text>10):  {good}")
    print(f"  ⚠️  Short text (>=2 opts):     {short_text}")
    print(f"  ⚠️  1 option only:             {few_options}")
    print(f"  ❌ No options:                 {no_options}")
    print(f"  ---")
    print(f"  With images: {with_images}")
    print(f"  Multi-answer: {multi_answer}")
    print(f"  Points: {by_points}")
    print(f"  With categories: {with_categories}")
    
    ids = [q["id"] for q in questions]
    if ids:
        expected = set(range(1, max(ids) + 1))
        missing = sorted(expected - set(ids))
        print(f"  Missing IDs ({len(missing)}): {missing[:30]}{'...' if len(missing) > 30 else ''}")
    
    # Show questions that still have problems
    bad_qs = [q for q in questions if len(q["options"]) == 0]
    if bad_qs:
        print(f"\n  No-option question IDs: {[q['id'] for q in bad_qs[:20]]}")
    
    # Save
    output = {
        "metadata": {
            "source": "МУП Србије — Управа саобраћајне полиције",
            "section": "Правила саобраћаја",
            "total_questions": len(questions),
            "questions_with_images": with_images,
            "parse_quality": {
                "good": good,
                "short_text": short_text,
                "few_options": few_options,
                "no_options": no_options,
            },
            "note": "Correct answers NOT included.",
        },
        "questions": questions,
    }
    
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {OUTPUT_FILE}")
    
    # Show previously broken questions to verify fix
    print("\n=== PREVIOUSLY BROKEN QUESTIONS ===")
    for qid in [14, 25, 35, 37, 49, 92, 96]:
        q = next((q for q in questions if q["id"] == qid), None)
        if q:
            status = "✅" if len(q["options"]) >= 2 and len(q["text"]) > 10 else "⚠️"
            print(f"{status} Q{qid}: opts={len(q['options'])} text={q['text'][:80]}...")
    
    print("\n=== SAMPLE GOOD QUESTIONS ===")
    for q in questions[:3]:
        print(json.dumps(q, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main()
