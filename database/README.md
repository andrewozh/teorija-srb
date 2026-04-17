# 🚗 Serbian Driving Exam Parser

Parser for the official Serbian driving theory exam questions published by the Ministry of Internal Affairs (МУП Србије).

## Goal

Build a structured, machine-readable dataset from the official MUP exam PDFs to power a personal learning app with features like:
- Practice quizzes / mock exams
- Favorites / bookmarks
- Progress tracking
- Spaced repetition

## Data Source

Official exam questions published by **МУП Србије — Управа саобраћајне полиције** (Traffic Police Directorate):

**[prezentacije.mup.gov.rs/usp/Vozacki ispit/](http://prezentacije.mup.gov.rs/usp/Vozacki%20ispit/Vozacki%20ispit.html)**

The full question database is split into 8 PDF sections:

| # | Section (Serbian) | Translation | Status |
|---|-------------------|-------------|--------|
| 1 | Уводно објашњење | Introductory explanation | ⬜ Not parsed |
| 2 | **Правила саобраћаја** | **Traffic rules** | ✅ **Parsed** |
| 3 | Саобраћајна сигнализација | Traffic signs & signals | ⬜ Not parsed |
| 4 | Возачи | Drivers | ⬜ Not parsed |
| 5 | Возила | Vehicles | ⬜ Not parsed |
| 6 | Основе безбедности саобраћаја и појмови | Safety basics & concepts | ⬜ Not parsed |
| 7 | Посебне мере и овлашћења | Special measures & authorizations | ⬜ Not parsed |
| 8 | Последице непоштовања прописа | Consequences of violations | ⬜ Not parsed |

Total question pool across all sections: **~2314 questions**.
On the actual exam: **41 random questions, 45 minutes, max 5–6 errors allowed**.

## What's Been Done

### Step 1: PDF Analysis

The source PDF (`Pravila saobracaja PDF.pdf`) is:
- 87 pages, A4 format
- **Two-column layout** — questions flow left column then right column per page
- Contains embedded images (traffic situation illustrations)
- Questions are numbered sequentially (1–797)
- Language: Serbian (Cyrillic script)

### Step 2: Text Extraction & Parsing

Tried multiple approaches:

1. **`pdftotext` (default mode)** — interleaved the two columns, producing garbled output
2. **`pdftotext -layout`** — preserved spatial layout but required manual column splitting by character position; produced ~786/797 questions but with cross-column contamination
3. **`PyMuPDF (fitz)` with coordinate-based extraction (v2)** — split each page into left/right halves using the PDF's coordinate system. Got 797/797 but 48 had missing options due to overlapping text blocks.
4. **`PyMuPDF` with block merging (v3)** ✅ — fixed three bugs:
   - **Overlapping blocks**: Question numbers like `"14."` appear as tiny blocks overlapping larger text blocks. Detected via vertical overlap and merged.
   - **Inline options**: Some options appear all on one line (`"а) 50 km/h, б) 70 km/h"`). Added pre-processing to split them.
   - **Category prefixes**: Category labels like `"D"` prefix option lines. Stripped before option detection.

### Step 3: Image Extraction

Extracted all content images from the PDF using PyMuPDF. Filtered out small decorative elements (logos, icons < 50px).

### Current Results — Section 2 (Правила саобраћаја)

| Metric | Value |
|--------|-------|
| Questions found | **797 / 797 (100%)** |
| Missing IDs | **0** |
| Fully parsed (text + ≥2 options) | **797 (100%)** |
| Questions with images | 420 |
| Multi-answer questions | 80 |
| With vehicle category tags | 204 |
| Point values: 2 pts / 3 pts | 600 / 197 |
| Images extracted | 437 |

## Output

```
driving-exam-parser/
├── README.md              ← this file
├── parse_v3.py            ← main parser (PyMuPDF-based, final)
├── parse_v2.py            ← previous version (kept for reference)
├── parse_questions.py     ← earlier pdftotext-based parser (kept for reference)
├── questions.json         ← structured output (589 KB)
├── pdf/                   ← source PDFs
│   └── Pravila saobracaja PDF.pdf
├── images/                ← extracted question images (437 PNGs, 141 MB)
│   ├── p001_03.png
│   ├── p001_04.png
│   └── ...
├── raw_text.txt           ← pdftotext extraction (for reference)
└── raw_layout.txt         ← pdftotext -layout extraction (for reference)
```

### JSON Schema

```jsonc
{
  "metadata": {
    "source": "МУП Србије — Управа саобраћајне полиције",
    "section": "Правила саобраћаја",
    "total_questions": 797
  },
  "questions": [
    {
      "id": 17,                          // question number from the PDF
      "text": "У ситуацији приказаној на слици поступање возача регулисано је:",
      "options": [
        { "letter": "а", "text": "постављеним саобраћајним знаком" },
        { "letter": "б", "text": "постављеном допунском таблом" },
        { "letter": "в", "text": "правилом саобраћаја, којим се регулише првенство пролаза" },
        { "letter": "г", "text": "светлосним саобраћајним знаком" }
      ],
      "points": 2,                       // 2 or 3
      "correct_answers_count": 2,        // how many options are correct
      "has_image": true,                 // references an illustration
      "categories": ["B", "C"]           // vehicle categories (optional)
    }
  ]
}
```

## What's Missing

### ❌ Correct Answers

The question PDFs do **not** mark which options are correct. A separate answer key PDF exists (password-protected for editing, but readable). **Next step: parse the answer key and merge.**

### ❌ Image-to-Question Mapping

Images are extracted and named by page (`p001_03.png` = page 1, image 3), but not yet linked to specific question IDs. Many questions reference "the situation shown in the picture" without the image being programmatically associated.

### ❌ Remaining 7 Sections

Only section 2 (Правила саобраћаја) has been parsed. The same parser should work on the other 7 PDFs with minimal changes.

## Tools & Dependencies

- **Python 3.10+**
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** (`pip install pymupdf`) — PDF text/image extraction with coordinate awareness
- **pdftotext** (from poppler-utils) — used for initial analysis, kept as fallback
- macOS (Homebrew for poppler)

## How to Run

```bash
# Install dependency
pip install pymupdf

# Run parser (expects the source PDF one level up)
cd driving-exam-parser
python3 parse_v2.py
```

The parser expects `Pravila saobracaja PDF.pdf` in the `pdf/` subdirectory.

## Notes

- The PDF header states: *"Забрањено је коришћење, односно повремено или стално умножавање базе података испитних питања или њених делова, било којим средствима и у било којој форми, у комерцијалне сврхе"* — reproduction of the question database is prohibited **for commercial purposes**. Personal/educational use is fine.
- Questions are available in Serbian (Cyrillic), Hungarian, and Albanian on the MUP website.
- The exam itself is taken through the MUP's online system at the driving school.
