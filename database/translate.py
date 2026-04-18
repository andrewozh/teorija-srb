#!/usr/bin/env python3
"""
Translate questions from Serbian to Russian using Claude API.

Sends each question as a single block (question text + all options)
so the model has full context for quality translation.

Adds `text_ru` to each question and `text_ru` to each option.
Skips already translated questions. Use --force to re-translate.

Requires ANTHROPIC_API_KEY environment variable.

Usage:
    python3 translate.py              # translate missing
    python3 translate.py --force      # re-translate all
    python3 translate.py --section pravila_saobracaja
    python3 translate.py --dry-run
"""

import json
import time
import argparse
import re
from pathlib import Path
import anthropic

QUESTIONS_JSON = Path(__file__).parent / "questions.json"

MODEL = "claude-sonnet-4-20250514"
SYSTEM_PROMPT = (
    "Переведи с сербского на русский. Это вопрос из экзамена по вождению. "
    "Внимательно работай с терминологией: если у термина есть точный аналог в ПДД РФ — используй его "
    "(например: возач=водитель, возило=транспортное средство, раскрсница=перекрёсток, "
    "пешачки прелаз=пешеходный переход, саобраћајна трака=полоса движения, "
    "претицање=обгон, обилажење=объезд, мимоилажење=встречный разъезд, "
    "ознака на коловозу=дорожная разметка, саобраћајни знак=дорожный знак, "
    "светлосни саобраћајни знак=светофор, зауставна трака=обочина). "
    "Если точного аналога нет — переводи дословно естественным русским языком. "
    "Сохрани буквы вариантов ответа (а, б, в, г, д). Ничего не добавляй от себя."
)

DELAY = 0.5  # seconds between API calls
SAVE_EVERY = 50


def needs_translation(q: dict, force: bool = False) -> bool:
    if q.get("is_removed"):
        return False
    if force:
        return True
    if "text_ru" not in q:
        return True
    if not all("text_ru" in o for o in q["options"]):
        return True
    return False


def combine_question(q: dict) -> str:
    """Combine question + options into one block."""
    text = q["text"]
    for o in q["options"]:
        text += f"\n{o['letter']}) {o['text']}"
    return text


def parse_translation(translated: str, options: list[dict]) -> tuple[str, list[str]]:
    """Split translated block back into question text + option texts."""
    letters = [o["letter"] for o in options]

    # Find where first option starts: "а) ..."
    first_pattern = rf'^{re.escape(letters[0])}\)'
    m = re.search(first_pattern, translated, re.MULTILINE)

    if m:
        q_text = translated[:m.start()].strip()
        opts_block = translated[m.start():]
    else:
        return translated.strip(), []

    # Split by option letters
    opt_texts = []
    for i, letter in enumerate(letters):
        if i + 1 < len(letters):
            pattern = rf'{re.escape(letter)}\)\s*(.*?)\s*(?={re.escape(letters[i+1])}\))'
            match = re.search(pattern, opts_block, re.DOTALL)
        else:
            pattern = rf'{re.escape(letter)}\)\s*(.*)'
            match = re.search(pattern, opts_block, re.DOTALL)

        if match:
            opt_texts.append(match.group(1).strip())
        else:
            opt_texts.append("")

    return q_text, opt_texts


def translate_question(client: anthropic.Anthropic, q: dict) -> bool:
    """Translate one question. Returns True on success."""
    combined = combine_question(q)

    for attempt in range(3):
        try:
            r = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": combined}],
            )
            translated = r.content[0].text

            q_text_ru, opt_texts_ru = parse_translation(translated, q["options"])
            q["text_ru"] = q_text_ru

            if len(opt_texts_ru) == len(q["options"]) and all(opt_texts_ru):
                for o, t_ru in zip(q["options"], opt_texts_ru):
                    o["text_ru"] = t_ru
            else:
                # Fallback: translate options individually
                for o in q["options"]:
                    if "text_ru" not in o or not o["text_ru"]:
                        try:
                            r2 = client.messages.create(
                                model=MODEL,
                                max_tokens=256,
                                system="Переведи с сербского на русский. Только перевод, ничего больше.",
                                messages=[{"role": "user", "content": o["text"]}],
                            )
                            o["text_ru"] = r2.content[0].text.strip()
                            time.sleep(DELAY)
                        except Exception:
                            o["text_ru"] = o["text"]

            return True
        except Exception as e:
            wait = (attempt + 1) * 5
            print(f"    Error on Q{q['id']}: {e}, retry in {wait}s")
            time.sleep(wait)

    return False


def main():
    parser = argparse.ArgumentParser(description="Translate questions to Russian via Claude")
    parser.add_argument("--section", help="Only translate this section")
    parser.add_argument("--force", action="store_true", help="Re-translate all (overwrite)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated")
    args = parser.parse_args()

    data = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
    questions = data["questions"]

    to_translate = [
        q for q in questions
        if needs_translation(q, args.force)
        and (not args.section or q.get("section") == args.section)
    ]

    print(f"Questions needing translation: {len(to_translate)}")

    if args.dry_run:
        for q in to_translate[:5]:
            print(f"  [{q['section']}] Q{q['id']}: {q['text'][:60]}...")
        if len(to_translate) > 5:
            print(f"  ... and {len(to_translate) - 5} more")
        return

    if not to_translate:
        print("Nothing to translate.")
        return

    client = anthropic.Anthropic()
    done = 0
    total_input = 0
    total_output = 0

    for q in to_translate:
        success = translate_question(client, q)
        done += 1

        if done % 10 == 0:
            print(f"  {done}/{len(to_translate)} — Q{q['id']} [{q['section']}]")

        if done % SAVE_EVERY == 0:
            QUESTIONS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"    Saved progress ({done})")

        time.sleep(DELAY)

    # Final save
    QUESTIONS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(questions)
    with_ru = sum(1 for q in questions if "text_ru" in q)
    print(f"\nDone! Translated {done} questions.")
    print(f"Coverage: {with_ru}/{total}")


if __name__ == "__main__":
    main()
