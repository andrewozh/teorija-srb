#!/usr/bin/env python3
"""
Fix points and last-option text in existing questions.json
by re-parsing from PDFs using the fixed parse_v3 logic.

Only updates: points, last option text.
Skips verified questions.
"""

import json
from pathlib import Path
from parse_v3 import parse_section

BASE_DIR = Path(__file__).parent
SOURCE_DIR = BASE_DIR / "source_17042026"
QUESTIONS_JSON = BASE_DIR / "questions.json"
SECTIONS_FILE = BASE_DIR / "sections.json"


def main():
    sections = json.loads(SECTIONS_FILE.read_text(encoding="utf-8"))
    data = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))

    # Index existing questions by (section, id)
    q_index = {}
    for q in data["questions"]:
        q_index[(q["section"], q["id"])] = q

    fixed_points = 0
    fixed_text = 0
    skipped = 0

    for sec in sections:
        pdf_path = SOURCE_DIR / sec["pdf"]
        if not pdf_path.exists() or sec["id"] == "uvodno_objasnjenje":
            continue

        # Re-parse with fixed logic
        new_questions = parse_section(pdf_path, sec["id"], sec["name"], sec["id"])

        for nq in new_questions:
            key = (sec["id"], nq["id"])
            oq = q_index.get(key)
            if not oq:
                continue
            if oq.get("is_verified"):
                skipped += 1
                continue

            # Fix points
            if oq["points"] != nq["points"]:
                print(f"  {sec['id']} Q{nq['id']}: points {oq['points']} → {nq['points']}")
                oq["points"] = nq["points"]
                fixed_points += 1

            # Fix last option text (where trailing digit was stuck)
            if oq["options"] and nq["options"]:
                old_last = oq["options"][-1]["text"]
                new_last = nq["options"][-1]["text"]
                if old_last != new_last and len(old_last) > len(new_last):
                    # Only fix if old text was longer (had trailing digit)
                    print(f"  {sec['id']} Q{nq['id']}: last opt «{old_last[-30:]}» → «{new_last[-30:]}»")
                    oq["options"][-1]["text"] = new_last
                    fixed_text += 1

    # Save
    QUESTIONS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nDone: {fixed_points} points fixed, {fixed_text} option texts fixed, {skipped} verified skipped")


if __name__ == "__main__":
    main()
