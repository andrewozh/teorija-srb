# 🚗 Serbian Driving Exam Parser

Parser for the official Serbian driving theory exam questions published by the Ministry of Internal Affairs (МУП Србије).

## Goal

Build a structured, machine-readable dataset from the official MUP exam PDFs to power a personal learning app with features like:
- Practice quizzes / mock exams
- Favorites / bookmarks
- Progress tracking
- Spaced repetition

## Data Sources

### Questions + Images + Flags
**[Pravila saobracaja PDF.pdf](http://prezentacije.mup.gov.rs/usp/Vozacki%20ispit/2.Pravila%20saobracaja/Pravila%20saobracaja%20PDF.pdf)** — official MUP publication.

Contains questions, answer options, images, vehicle categories, point values, and colored background highlights indicating question status (removed/changed/new).

### Correct Answers
**[SVA-PITANJA-sa-resenjima.pdf](https://autoskolasljivic.com/wp-content/uploads/2020/09/SVA-PITANJA-sa-resenjima.pdf)** — all questions with solutions.

Correct answers are marked with red circles (vector ellipses) around the option letter. Detected via PDF vector path analysis.

## Results — Section "Правила саобраћаја"

| Metric | Value |
|--------|-------|
| Questions parsed | **797 / 797 (100%)** |
| Correct answers extracted | **795 / 797 (99.7%)** |
| Images extracted & linked | **420 / 420 (100%)** |
| Multi-answer questions | 80 |
| With vehicle category tags | 204 |
| Point values: 2 pts / 3 pts | 600 / 197 |

### Question Status Flags

The official PDF highlights modified questions with colored backgrounds:

| Flag | Count | Meaning |
|------|-------|---------|
| `is_removed` | 3 | Deleted from exam database |
| `is_changed` | 47 | Modified question or answers |
| `is_new` | 6 | Recently added to exam |
| No flag | 741 | Original, unchanged |

The 2 questions without answers (Q223, Q560) are both `is_removed` — no answer exists because they're no longer in the exam.

## Output

```
database/
├── README.md
├── Makefile               ← all commands
├── parse_v3.py            ← question parser (PyMuPDF)
├── extract_answers.py     ← answer extractor (circle detection)
├── questions.json         ← structured output
├── source_17042026/       ← source PDFs
│   ├── Pravila saobracaja PDF.pdf
│   └── SVA-PITANJA-sa-resenjima.pdf
└── images/                ← extracted question images (440 PNGs)
```

### JSON Schema

```jsonc
{
  "metadata": {
    "source": "МУП Србије — Управа саобраћајне полиције",
    "section": "Правила саобраћаја",
    "total_questions": 797,
    "answers_coverage": "795/797"
  },
  "questions": [
    {
      "id": 18,
      "text": "У ситуацији приказаној на слици поступање возача регулисано је:",
      "options": [
        { "letter": "а", "text": "постављеним саобраћајним знаком" },
        { "letter": "б", "text": "правилом саобраћаја, којим се регулише првенство пролаза" },
        { "letter": "в", "text": "ознакама на коловозу" },
        { "letter": "г", "text": "светлосним саобраћајним знаком" }
      ],
      "points": 2,
      "correct_answers_count": 2,
      "has_image": true,
      "image": "p003_y0549.png",
      "correct_answers": ["б", "г"],
      "categories": ["B", "C"],
      "is_changed": true           // optional flag
    }
  ]
}
```

## Usage

```bash
cd database/
make install    # install Python dependencies (pymupdf, pikepdf)
make download   # download source PDFs into source_17042026/
make parse      # parse questions → questions.json + images/
make answers    # extract correct answers → merge into questions.json
make stats      # show dataset stats
make validate   # check data integrity
make clean-all  # remove all generated files
```

## How It Works

### Question Parsing (`parse_v3.py`)

The MUP PDF uses a two-column layout with embedded images. Challenges solved:

1. **Column splitting** — PyMuPDF coordinate-based extraction, splitting each page at `width/2`
2. **Overlapping text blocks** — question numbers (`"14."`) appear as separate tiny blocks overlapping the question text block. Detected via vertical overlap and merged before parsing.
3. **Inline options** — some options appear all on one line (`"а) 50 km/h, б) 70 km/h"`). Pre-processing splits them.
4. **Image reuse** — same image xref placed at multiple positions (shared by related questions). Each placement gets its own entry.
5. **Status flags** — colored background fills detected as vector rectangles: red=removed, yellow=changed, green=new.

### Answer Extraction (`extract_answers.py`)

The answers PDF marks correct options with red vector circles (~12×11pt ellipses) drawn around the option letter. The extractor:

1. Finds the "ПРАВИЛА САОБРАЋАЈА" section by page scan
2. Detects small curved vector paths (circles) on each page
3. Matches each circle to the nearest option letter by coordinate proximity
4. Handles both single-column and grid (2×2) option layouts

## Remaining Sections

The full exam has ~2314 questions across 8 sections. Only section 2 is parsed:

| # | Section | Status |
|---|---------|--------|
| 1 | Уводно објашњење | ⬜ |
| 2 | **Правила саобраћаја** | ✅ |
| 3 | Саобраћајна сигнализација | ⬜ |
| 4 | Возачи | ⬜ |
| 5 | Возила | ⬜ |
| 6 | Основе безбедности саобраћаја и појмови | ⬜ |
| 7 | Посебне мере и овлашћења | ⬜ |
| 8 | Последице непоштовања прописа | ⬜ |

## Notes

- The PDF header states reproduction is prohibited **for commercial purposes**. Personal/educational use is fine.
- On the actual exam: **41 random questions, 45 minutes, max 5–6 errors allowed**.
- Questions are in Serbian (Cyrillic). Also available in Hungarian and Albanian on the MUP website.
