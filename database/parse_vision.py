#!/usr/bin/env python3
"""
Parse question screenshots using Claude Vision API.

Usage:
  python3 parse_vision.py <section> <questions...>

Examples:
  python3 parse_vision.py 01_osnove_bezbednosti 1 5 42
  python3 parse_vision.py 03_vozila 124-136
  python3 parse_vision.py 04_signalizacija 1-10 50 100
"""

import sys
import json
import base64
import shutil
from pathlib import Path

import anthropic

BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR.parent / "db_new"
RULES_PATH = DB_DIR / "PARSING_RULES.md"

MODEL = "claude-sonnet-4-6"


def parse_question_args(args: list[str]) -> list[int]:
    """Parse question numbers from args like '1', '5', '10-20'."""
    numbers = []
    for arg in args:
        if "-" in arg:
            start, end = arg.split("-", 1)
            numbers.extend(range(int(start), int(end) + 1))
        else:
            numbers.append(int(arg))
    return sorted(set(numbers))


def build_prompt() -> str:
    rules = RULES_PATH.read_text(encoding="utf-8")
    return f"""{rules}

---

Parse this question screenshot according to the rules above.
Copy all text EXACTLY as shown — character by character. Do NOT transliterate between Cyrillic and Latin scripts.
Return ONLY valid JSON, no markdown fences, no commentary.
"""


def call_vision(image_path: Path, prompt: str) -> dict:
    """Send image to Claude Vision, return parsed JSON."""
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    suffix = image_path.suffix.lower()
    media_type = "image/png" if suffix == ".png" else "image/jpeg"

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )

    text = response.content[0].text.strip()
    # Strip markdown fences if model adds them despite instructions
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
        text = text.strip()

    # Fix unescaped quotes inside JSON string values
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        fixed = re.sub(
            r'(?<=: ")(.*?)(?="[,}\]\n])',
            lambda m: m.group(0).replace('\\"', '"').replace('"', '\\"') if '"' in m.group(0) else m.group(0),
            text, flags=re.DOTALL
        )
        return json.loads(fixed)


# Serbian Latin → Cyrillic post-processing
_LAT2CYR_DIGRAPHS = {"dž": "џ", "Dž": "Џ", "DŽ": "Џ", "lj": "љ", "Lj": "Љ", "LJ": "Љ", "nj": "њ", "Nj": "Њ", "NJ": "Њ"}
_LAT2CYR = str.maketrans({
    'a': 'а', 'b': 'б', 'c': 'ц', 'č': 'ч', 'ć': 'ћ', 'd': 'д', 'đ': 'ђ',
    'e': 'е', 'f': 'ф', 'g': 'г', 'h': 'х', 'i': 'и', 'j': 'ј', 'k': 'к',
    'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с',
    'š': 'ш', 't': 'т', 'u': 'у', 'v': 'в', 'z': 'з', 'ž': 'ж',
    'A': 'А', 'B': 'Б', 'C': 'Ц', 'Č': 'Ч', 'Ć': 'Ћ', 'D': 'Д', 'Đ': 'Ђ',
    'E': 'Е', 'F': 'Ф', 'G': 'Г', 'H': 'Х', 'I': 'И', 'J': 'Ј', 'K': 'К',
    'L': 'Л', 'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р', 'S': 'С',
    'Š': 'Ш', 'T': 'Т', 'U': 'У', 'V': 'В', 'Z': 'З', 'Ž': 'Ж',
})

def latin_to_cyrillic(text: str) -> str:
    """Convert Serbian Latin to Cyrillic. Preserves digits and punctuation."""
    for lat, cyr in _LAT2CYR_DIGRAPHS.items():
        text = text.replace(lat, cyr)
    return text.translate(_LAT2CYR)

def fix_cyrillic(result: dict) -> dict:
    """Post-process: convert any Latin text to Cyrillic in text fields."""
    if "text" in result:
        result["text"] = latin_to_cyrillic(result["text"])
    for opt in result.get("options", []):
        if "text" in opt:
            opt["text"] = latin_to_cyrillic(opt["text"])
    return result


def process_question(section: str, q_num: int, prompt: str):
    """Process a single question: call Vision, save results."""
    screenshot = DB_DIR / section / f"q{q_num:03d}.png"
    if not screenshot.exists():
        print(f"  ✗ Q{q_num}: screenshot not found ({screenshot})")
        return False

    out_dir = DB_DIR / section / f"q{q_num:03d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy original screenshot
    shutil.copy2(screenshot, out_dir / "screenshot.png")

    # Call Vision API and fix Cyrillic
    result = fix_cyrillic(call_vision(screenshot, prompt))

    # Crop image row if coordinates provided
    row_top = result.get("image_row_top")
    row_bottom = result.get("image_row_bottom")
    if row_top is not None and row_bottom is not None and result.get("has_image"):
        from PIL import Image
        img = Image.open(screenshot)
        w, h = img.size
        cropped = img.crop((0, int(h * row_top), w, int(h * row_bottom)))
        cropped.save(out_dir / "image.png")

    # Save JSON
    (out_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Summary
    q_text = result.get("text", "")[:60]
    correct = result.get("correct_answers", [])
    pts = result.get("points", "?")
    has_img = "🖼" if result.get("has_image") else "  "
    status = result.get("status") or ""
    if status:
        status = f" [{status}]"
    print(f"  ✓ Q{q_num}: {has_img} pts={pts} ans={correct}{status}  «{q_text}…»")
    return True


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    section = sys.argv[1]
    section_dir = DB_DIR / section
    if not section_dir.exists():
        print(f"Section directory not found: {section_dir}")
        sys.exit(1)

    questions = parse_question_args(sys.argv[2:])
    prompt = build_prompt()

    print(f"Section: {section}")
    print(f"Questions: {questions}")
    print()

    ok = 0
    for q_num in questions:
        try:
            if process_question(section, q_num, prompt):
                ok += 1
        except json.JSONDecodeError as e:
            print(f"  ✗ Q{q_num}: invalid JSON from model: {e}")
        except Exception as e:
            print(f"  ✗ Q{q_num}: {e}")

    print(f"\nDone: {ok}/{len(questions)} parsed")


if __name__ == "__main__":
    main()
