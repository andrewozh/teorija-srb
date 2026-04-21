# Serbian Driving Exam Question Parsing Rules

## Question Structure

Each question is a table with a thick outer border. Inside there are 2 or 3 rows:

### Question WITHOUT image (2 rows):
```
┌──────────┬─────────────────────────────────────┐
│  Q num   │  Question text                      │
│          │                                     │
├──────────┼─────────────────────────┬────────────┤
│          │  а) answer option       │            │
│ Categ.   │  б) answer option       │   Points   │
│ (A,B,C…) │  в) answer option       │   (1-4)    │
└──────────┴─────────────────────────┴────────────┘
```

### Question WITH image (3 rows):
```
┌──────────┬─────────────────────────────────────┐
│  Q num   │  Question text                      │
│          │                                     │
├──────────┼─────────────────────────────────────┤
│          │  [IMAGE / PHOTO / DIAGRAM]           │
│          │  (may include captions/numbers)      │
├──────────┼─────────────────────────┬────────────┤
│          │  а) answer option       │            │
│ Categ.   │  б) answer option       │   Points   │
│ (A,B,C…) │  в) answer option       │   (1-4)    │
└──────────┴─────────────────────────┴────────────┘
```

## What to Extract

### 1. Question number
- **Where:** top-left cell
- **Format:** integer, 1 to ~800

### 2. Question text
- **Where:** top row, right cell
- **Format:** Serbian text (Cyrillic script)
- **CRITICAL:** Copy text EXACTLY as shown, character by character. Do NOT transliterate between Cyrillic and Latin. Do NOT translate.
- If there is a note about multiple correct answers like `(Заокружити два тачна одговора)` or `(Заокружити три тачна одговора)`, remove it from the text and return the count separately in `correct_answers_count`.

### 3. Image
- **Where:** the middle row of the table (only present in 3-row questions)
- **Return:** `has_image: true/false`. If true, return `image_row_top` and `image_row_bottom` — vertical positions of the middle row's top and bottom edges, as floats 0.0-1.0 relative to the full screenshot height.
- These are the positions of the thin horizontal lines that separate the middle row from the text row above and the answers row below. The entire middle row is the image area.
- Can be: road photo, intersection diagram, traffic sign, schematic, etc.
- Sometimes multiple numbered images (1, 2, 3, 4) in a row

### 4. Answer options
- **Where:** bottom row, center cell
- **Format:** letters `а)`, `б)`, `в)`, sometimes `г)`, `д)`, `е)` + text
- Usually 3 options, sometimes 2, 4 or more
- **CRITICAL:** Copy option text EXACTLY as shown. Do NOT transliterate or translate.
- **Correct answer:** marked with a red circle around the option letter. Return the list of circled letters.
- Answer options are always text-only.

### 5. Categories
- **Where:** bottom-left cell
- **Format:** one or more bold letters: `A`, `B`, `C`, `D`, `F`, `M`
- **If cell is empty** — question applies to ALL categories. Return empty array.

### 6. Points
- **Where:** bottom-right cell
- **Format:** bold digit: `1`, `2`, `3`, or `4`

### 7. Background color (question status)
- **Yellow background** → question was modified: `"changed"`
- **Red background** → question removed from exam: `"removed"`
- **Green background** → new question: `"new"`
- **Blue text color** → answer not in legislation: `"blue"`
- **No background / normal** → `null`

## Common Mistakes to Avoid

**Transliteration:** Serbian uses both Cyrillic and Latin scripts. The exam PDFs use Cyrillic. You MUST copy text exactly as printed. Do NOT convert between scripts.

WRONG: `"uniformisani policijski službenici"` (Latin)
WRONG: `"uniformисани полицијски службеници"` (mixed)
CORRECT: `"униформисани полицијски службеници"` (Cyrillic as printed)

## Example

Input: a screenshot of question 2 from the exam.

Correct output:
```json
{
  "question_number": 2,
  "text": "На путу ван насеља, као и на путу у насељу ноћу или у условима смањене видљивости када је место на коме се возило зауставља недовољно осветљено, возач је дужан:",
  "correct_answers_count": 1,
  "has_image": false,
  "image_row_top": null,
  "image_row_bottom": null,
  "options": [
    {"letter": "а", "text": "само да возило обележи сигурносним троуглом,"},
    {"letter": "б", "text": "само да укључи све показиваче правца,"},
    {"letter": "в", "text": "да возило обележи сигурносним троуглом и да укључи све показиваче правца."}
  ],
  "correct_answers": ["в"],
  "categories": ["B", "C", "D", "F"],
  "points": 2,
  "status": null
}
```

Note: all text is in Cyrillic, exactly as printed in the exam.

## Response Format (JSON)

```json
{
  "question_number": 42,
  "text": "Текст вопроса на сербском языке",
  "correct_answers_count": 1,
  "has_image": true,
  "image_row_top": 0.08,
  "image_row_bottom": 0.75,
  "options": [
    {"letter": "а", "text": "текст варианта"},
    {"letter": "б", "text": "текст варианта"},
    {"letter": "в", "text": "текст варианта"}
  ],
  "correct_answers": ["б"],
  "categories": ["B", "C", "D", "F"],
  "points": 2,
  "status": null
}
```

### Field details:
- `correct_answers_count`: from the "(Заокружити два/три тачна одговора)" note. Default `1`.
- `has_image`: `true` if the question table has 3 rows (with an image row in the middle), `false` if only 2 rows.
- `image_row_top`: vertical position where the middle (image) row starts, as float 0.0-1.0. `null` if `has_image` is false.
- `image_row_bottom`: vertical position where the middle (image) row ends, as float 0.0-1.0. `null` if `has_image` is false.
- `correct_answers`: array of letters circled in red. E.g. `["а", "в"]`.
- `categories`: empty array `[]` if applies to all categories.
- `status`: `"changed"`, `"removed"`, `"new"`, `"blue"`, or `null`.
