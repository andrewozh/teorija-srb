#!/usr/bin/env python3
"""
Translate questions from Serbian to Russian using Google Translate.

Adds `text_ru` field to each question and `text_ru` to each option.
Skips questions that already have translations.

Usage:
    python3 translate.py              # translate all
    python3 translate.py --section pravila_saobracaja  # translate one section
    python3 translate.py --dry-run    # show what would be translated
"""

import json
import time
import argparse
import sys
from pathlib import Path
from deep_translator import GoogleTranslator

QUESTIONS_JSON = Path(__file__).parent / "questions.json"

BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 1.0


def needs_translation(q: dict) -> bool:
    """Check if a question needs translation."""
    if q.get("is_removed"):
        return False
    if "text_ru" in q:
        # Check if options also have translations
        if all("text_ru" in o for o in q["options"]):
            return False
    return True


def translate_batch(texts: list[str]) -> list[str]:
    """Translate a batch of texts. Retries on failure."""
    translator = GoogleTranslator(source="sr", target="ru")
    results = []
    for text in texts:
        for attempt in range(3):
            try:
                translated = translator.translate(text)
                results.append(translated if translated else text)
                break
            except Exception as e:
                wait = (attempt + 1) * 3
                print(f"    Error on '{text[:30]}...': {e}, retry in {wait}s")
                time.sleep(wait)
        else:
            results.append(text)
        time.sleep(0.2)
    return results


def translate_questions(section_filter: str | None = None, dry_run: bool = False):
    data = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
    questions = data["questions"]

    # Filter
    to_translate = []
    for q in questions:
        if section_filter and q.get("section") != section_filter:
            continue
        if needs_translation(q):
            to_translate.append(q)

    print(f"Questions needing translation: {len(to_translate)}")
    if dry_run:
        for q in to_translate[:10]:
            print(f"  [{q['section']}] Q{q['id']}: {q['text'][:60]}...")
        if len(to_translate) > 10:
            print(f"  ... and {len(to_translate) - 10} more")
        return

    if not to_translate:
        print("Nothing to translate.")
        return

    translated_count = 0

    # Collect all texts to translate: question texts + option texts
    # Process in batches
    i = 0
    while i < len(to_translate):
        batch_questions = to_translate[i:i + BATCH_SIZE]
        
        # Gather all texts for this batch
        texts = []
        text_map = []  # (question_index, 'text' | ('option', option_index))
        
        for qi, q in enumerate(batch_questions):
            if "text_ru" not in q:
                texts.append(q["text"])
                text_map.append((qi, "text"))
            for oi, opt in enumerate(q["options"]):
                if "text_ru" not in opt:
                    texts.append(opt["text"])
                    text_map.append((qi, ("option", oi)))

        if texts:
            print(f"  Batch {i // BATCH_SIZE + 1}: translating {len(texts)} texts (Q{batch_questions[0]['id']}-Q{batch_questions[-1]['id']})...")
            translations = translate_batch(texts)

            # Apply translations
            for (qi, target), translated_text in zip(text_map, translations):
                q = batch_questions[qi]
                if target == "text":
                    q["text_ru"] = translated_text
                else:
                    _, oi = target
                    q["options"][oi]["text_ru"] = translated_text

            translated_count += len(batch_questions)
            time.sleep(DELAY_BETWEEN_BATCHES)

        i += BATCH_SIZE

        # Save periodically (every 100 questions)
        if translated_count % 100 < BATCH_SIZE and translated_count > 0:
            QUESTIONS_JSON.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"    Saved progress ({translated_count} questions)")

    # Final save
    QUESTIONS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nDone! Translated {translated_count} questions.")

    # Stats
    total = len(questions)
    with_ru = sum(1 for q in questions if "text_ru" in q)
    print(f"Coverage: {with_ru}/{total} questions have Russian translations")


def main():
    parser = argparse.ArgumentParser(description="Translate questions to Russian")
    parser.add_argument("--section", help="Only translate this section")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated")
    args = parser.parse_args()

    translate_questions(section_filter=args.section, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
