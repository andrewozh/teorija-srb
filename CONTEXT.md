# Project Context for AI Continuation

## Project: Serbian Driving Theory Exam App

### Repository Structure
```
~/dev/driving-exam-parser/
├── database/                    ← PDF parsing, data extraction, verification
│   ├── Makefile                 ← make parse, make answers, make translate, etc
│   ├── sections.json            ← section definitions (order, PDF filenames, answer headers)
│   ├── questions.json           ← THE DATABASE (2309 questions, all data)
│   ├── questions.backup.json    ← backup before last rebuild
│   ├── parse_v3.py              ← main question parser (PyMuPDF)
│   ├── extract_answers.py       ← correct answer extractor (red circles in SVA PDF)
│   ├── translate.py             ← Serbian→Russian translation (Claude API)
│   ├── verify.py                ← web verification/editing tool (localhost:8765)
│   ├── verify_log.jsonl         ← changelog of manual edits
│   ├── source_17042026/         ← source PDFs (downloaded via make download)
│   │   ├── Pravila saobracaja PDF.pdf
│   │   ├── Saobracajna signalizacija PDF.pdf
│   │   ├── Vozaci PDF.pdf
│   │   ├── Vozila PDF.pdf
│   │   ├── Osnove bezbednosti saobracaja i pojmovi i izrazi PDF.pdf
│   │   ├── Posebne mere i ovlascenja PDF.pdf
│   │   ├── Posledice nepostovanja propisa PDF.pdf
│   │   ├── Objasnjenje ispitnih zadataka PDF.pdf
│   │   ├── Objasnjenje izmene ispitnih pitanja PDF.pdf
│   │   └── SVA-PITANJA-sa-resenjima.pdf      ← answers PDF (red circles)
│   ├── saobracajData/           ← 3rd party parsed data (1701 questions, all with answers)
│   │   ├── allQuestions.json    ← {qcId, Text, Choices[{Text, isCorrect}], ...}
│   │   ├── categories.json
│   │   └── img/                 ← their images
│   └── images/                  ← extracted question images
├── app/                         ← Svelte PWA (SvelteKit + static adapter)
│   ├── Makefile                 ← make dev, make build, make deploy, make sync-data
│   ├── SPEC.md                  ← feature spec
│   ├── svelte.config.js         ← base: '/driving-theory-srb'
│   ├── src/
│   │   ├── lib/
│   │   │   ├── types.ts         ← Question, Option, Settings, Lang, etc
│   │   │   ├── store.ts         ← localStorage persistence (progress, bookmarks, exams)
│   │   │   ├── data.ts          ← load questions.json, helpers (qText, oText, etc)
│   │   │   ├── i18n.ts          ← UI translations (Serbian/Russian)
│   │   │   ├── nav.ts           ← page title store
│   │   │   ├── tokens.css       ← design tokens (colors, fonts, spacing)
│   │   │   └── components/      ← Icon, Header, ProgressBar, Tag, AnswerOption, QuestionPills
│   │   └── routes/              ← SvelteKit pages
│   │       ├── +page.svelte     ← Home (welcome/main)
│   │       ├── +layout.svelte   ← global shell
│   │       ├── practice/        ← training flow
│   │       ├── exam/            ← mock exam
│   │       ├── mistakes/        ← wrong answers review
│   │       ├── statistics/      ← progress stats
│   │       ├── settings/        ← theme, language, import/export
│   │       └── about/           ← app info
│   └── static/
│       ├── questions.json       ← COPY of database/questions.json (via make sync-data)
│       ├── images/              ← COPY of database/images/ (via make sync-data)
│       ├── manifest.json
│       ├── icon-192.png         ← Serbian cross icon
│       └── icon-512.png
├── Theory-handoff/              ← UI design from Claude Designer
│   └── theory/project/          ← design HTML/CSS/JS prototypes
├── .gitignore
└── CONTEXT.md                   ← THIS FILE
```

### Database Format (questions.json)
```json
{
  "metadata": {
    "source": "МУП Србије",
    "sections": [{"id": "osnove_bezbednosti", "name": "...", "questions": 170}, ...],
    "total_questions": 2309
  },
  "questions": [
    {
      "id": 1,                              // question number (unique within section)
      "section": "pravila_saobracaja",       // section ID
      "text": "Question text in Serbian",
      "text_ru": "Translation to Russian",   // optional, from translate.py
      "options": [
        {"letter": "а", "text": "option text", "text_ru": "..."},
        {"letter": "б", "text": "..."},
        {"letter": "в", "text": "..."}
      ],
      "points": 2,                           // 1, 2, 3, or 4
      "correct_answers_count": 1,            // how many correct answers
      "correct_answers": ["б"],              // from extract_answers.py
      "has_image": true,
      "image": "p001_y0197.png",             // filename in images/
      "categories": ["B", "C"],              // vehicle categories, [] = all
      "is_removed": true,                    // optional flags from colored backgrounds
      "is_changed": true,
      "is_new": true
    }
  ]
}
```

### Sections (7 total, ordered as in answers PDF)
| ID | Name | Questions | Max ID |
|----|------|-----------|--------|
| osnove_bezbednosti | Основе безбедности саобраћаја и појмови | 170 | 170 |
| vozaci | Возачи | 216 | 216 |
| vozila | Возила | 365 | 365 |
| saobracajna_signalizacija | Саобраћајна сигнализација | 524 | 524 |
| pravila_saobracaja | Правила саобраћаја | 797 | 797 |
| posebne_mere | Посебне мере и овлашћења | 61 | 61 |
| posledice | Последице непоштовања прописа | 182 | 182 |

### Vehicle Categories
A (motorcycles), B (cars), C (trucks), D (buses), F (tractors)
Questions without categories = for all categories.

### Current State & Known Issues

**What works:**
- 2309 questions parsed from 7 official MUP PDFs
- Verification web tool (verify.py) at localhost:8765
- PWA app deployed to https://andrewozh.github.io/driving-theory-srb/
- Translations to Russian (~1756 via Claude API)
- App has carousel question view, mock exam, bookmarks, dark/light theme

**What's broken (needs fixing):**
1. **~30 questions with garbled text** — caused by table-layout pages in PDFs where PyMuPDF splits text into tiny fragments. Affected pages:
   - Vozaci page 15 (Q173-185)
   - Vozila pages 10, 23
   - Signalizacija pages 20, 34, 35, 44, 74

2. **Wrong points** on many questions — parser doesn't detect bold font (point value indicator)

3. **Missing categories** — when category letter (A/B/C/D/F) is inside a text block, not standalone

4. **Broken images** — on table pages, images are split into tiny xref fragments. Normal pages work fine.

5. **Answers not loaded** — `make answers` not run on current database rebuild

6. **9 problem questions**: vozaci Q24 (no options), posledice Q9 (1 option), vozila Q123/Q330 (empty), vozila Q213 (22 options = merged), etc.

### Solution In Progress: Claude Vision Pipeline

**The plan:** Send each PDF page as an image to Claude Vision API to get perfect parsing.

**Tested successfully on Vozila page 10 (Q124-136):**
- Sent rendered page (200 DPI) + our parsed data as prompt
- Claude returned perfect JSON: text, options, points, categories, has_image
- Cost: ~$0.04 per page, ~$10 for all 250 pages
- Results applied to questions.json via simple Python script

**Image extraction approach (tested on page 23):**
- Question boxes have black rectangular borders in the PDF
- Detect borders via vertical bars: black filled rects with `width < 3, height > 20`
- Left column borders at x ≈ 22, right column at x ≈ 571
- Merge consecutive touching bars by y-coordinate → each segment = one question
- Crop from rendered page (200 DPI) using PIL
- **Issue:** left boundary slightly cut off, needs x offset adjustment (-3px or so)

**Code for border detection:**
```python
import fitz
doc = fitz.open('source_17042026/Vozila PDF.pdf')
page = doc[page_number]
drawings = page.get_drawings()
black_rects = [d['rect'] for d in drawings if d.get('fill') == (0, 0, 0)]
# Vertical bars at x~22 (left col left edge) and x~571 (right col right edge)
v_bars = [r for r in black_rects if r.width < 3 and r.height > 20]
# Merge touching bars, crop from pixmap
```

### How to Work With This Project

**Rebuild database from scratch:**
```bash
cd database/
make clean-all          # delete questions.json + images/
make parse              # parse all 7 PDFs → questions.json + images/
make answers            # extract correct answers from SVA PDF → merge into questions.json
```

**Run verification tool:**
```bash
cd database/
python3 verify.py       # opens http://localhost:8765
```

**Build and deploy app:**
```bash
cd app/
make sync-data          # copy questions.json + images from database/
make build              # build static site
make deploy             # push to GitHub Pages (gh-pages branch)
```

**Translate questions:**
```bash
cd database/
python3 translate.py --force   # re-translate all via Claude API
# Requires ANTHROPIC_API_KEY in ~/.bashrc
```

### API Keys (in ~/.bashrc)
- `ANTHROPIC_API_KEY` — for Claude (translation + vision)
- `OPENAI_API_KEY` — for OpenAI (tested but not used)

### Important Files to Read First
1. `database/parse_v3.py` — the parser, all extraction logic
2. `database/extract_answers.py` — answer extraction from red circles
3. `database/verify.py` — web verification tool
4. `database/sections.json` — section config
5. `app/src/lib/types.ts` — TypeScript types (Question, Option, etc)
6. `app/src/lib/store.ts` — app state management

### Next Steps
1. Build Vision pipeline script: render each page → Claude Vision → update questions.json
2. Build image extraction: detect question borders → crop from page render
3. Run `make answers` to fill correct answers
4. Run translate.py to fill Russian translations
5. Fix remaining problem questions via verify.py
6. Deploy updated app
