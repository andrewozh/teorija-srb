# Project Context for AI Continuation

## Project: Serbian Driving Theory Exam App — "Teorija"

**Version:** 0.8.2-beta
**Deployed:** https://andrewozh.github.io/driving-theory-srb/
**Repo:** https://github.com/andrewozh/teorija-srb

### Repository Structure
```
~/dev/driving-exam-parser/
├── database/                    ← PDF parsing, data extraction, verification
│   ├── Makefile                 ← make parse, make answers, make translate, etc
│   ├── sections.json            ← section definitions (order, PDF filenames, answer headers)
│   ├── questions.json           ← THE DATABASE (2315 questions, 2288 active)
│   ├── questions.backup.json    ← backup
│   ├── parse_v3.py              ← main question parser (PyMuPDF) — preserves verified questions
│   ├── extract_answers.py       ← correct answer extractor (red circles in SVA PDF) — skips verified
│   ├── translate.py             ← Serbian→Russian translation (Claude API, model: claude-sonnet-4-6)
│   ├── parse_vision.py          ← Claude Vision parser for question screenshots
│   ├── crop_questions.py        ← crop question screenshots from SVA PDF (thick h-bar detection)
│   ├── fix_points.py            ← fix points and last-option text from re-parsed PDFs
│   ├── verify.py                ← web verification/editing tool (localhost:8765)
│   ├── verify_log.jsonl         ← changelog of manual edits
│   ├── source_17042026/         ← source PDFs
│   │   └── SVA-PITANJA-sa-resenjima.pdf  ← all sections merged + answers (red circles)
│   └── images/                  ← extracted question images (967 files, WebP format)
├── db_new/                      ← question screenshots organized by section
│   ├── PARSING_RULES.md         ← English prompt for Claude Vision parsing
│   ├── 01_osnove_bezbednosti/   ← 170 screenshots (q001.png – q170.png)
│   ├── 02_vozaci/               ← 216 screenshots
│   ├── 03_vozila/               ← 365 screenshots
│   ├── 04_signalizacija/        ← 524 screenshots
│   ├── 05_pravila_saobracaja/   ← 797 screenshots
│   ├── 06_posebne_mere/         ← 61 screenshots
│   └── 07_posledice/            ← 182 screenshots
├── app/                         ← Svelte 5 PWA (SvelteKit + static adapter)
│   ├── Makefile                 ← make dev, make build, make deploy (includes sync-data)
│   ├── svelte.config.js         ← base: '/driving-theory-srb'
│   ├── src/
│   │   ├── lib/
│   │   │   ├── types.ts         ← Question, Option, Settings, Lang, Category, QuestionProgress (with streak)
│   │   │   ├── store.ts         ← localStorage persistence, recordAnswer (tracks streak), getMistakeStatus
│   │   │   ├── data.ts          ← loadQuestions, getActiveQuestions (category filter), SRS algorithm, exam generation
│   │   │   ├── topics.ts        ← topic definitions with hints (section 1 only, 12 topics)
│   │   │   ├── i18n.ts          ← UI translations (sr/ru)
│   │   │   ├── tokens.css       ← design tokens, .beta-badge
│   │   │   └── components/
│   │   │       ├── QuestionCarousel.svelte ← SHARED question view (practice, bookmarks, mistakes, exam, learn)
│   │   │       ├── AnswerOption.svelte     ← answer states: idle, selected, correct, wrong, muted, missed (orange)
│   │   │       ├── QuestionPills.svelte    ← smooth scroll with padding
│   │   │       ├── Header.svelte
│   │   │       ├── Icon.svelte
│   │   │       ├── ProgressBar.svelte
│   │   │       └── Tag.svelte
│   │   └── routes/
│   │       ├── +page.svelte     ← Home (hero: learning, sec: all questions)
│   │       ├── +layout.svelte   ← global shell, __toggleLang with fade animation
│   │       ├── learn/           ← SRS assisted learning page
│   │       ├── practice/        ← "All questions" — sections → topics/chunks → carousel
│   │       ├── exam/            ← mock exam (41Q, 100pts, ≥80 to pass, forced Serbian)
│   │       ├── mistakes/        ← wrong answers (red=wrong, orange=recovering)
│   │       ├── statistics/      ← progress stats
│   │       ├── settings/        ← theme(system default), language, category(B default), import/export
│   │       └── about/           ← version, sources (MUP + autoskola), section breakdown, author card
│   └── static/
│       ├── questions.json       ← COPY of database/questions.json (via make sync-data)
│       └── images/              ← COPY of database/images/ (WebP)
├── Theory-handoff/              ← UI design from Claude Designer
└── CONTEXT.md                   ← THIS FILE
```

### Database Format (questions.json)
```json
{
  "metadata": {
    "source": "МУП Србије — Управа саобраћајне полиције",
    "sections": [{"id": "osnove_bezbednosti", "name": "...", "questions": 170}, ...],
    "total_questions": 2315
  },
  "questions": [
    {
      "id": 1,
      "section": "pravila_saobracaja",
      "text": "Question text in Serbian",
      "text_ru": "Translation to Russian",
      "options": [
        {"letter": "а", "text": "option text", "text_ru": "russian"},
        {"letter": "б", "text": "..."},
        {"letter": "в", "text": "..."}
      ],
      "points": 2,                    // 1, 2, 3, or 4
      "correct_answers_count": 1,
      "correct_answers": ["б"],
      "has_image": true,
      "image": "p001_y0197.webp",     // WebP format in images/
      "categories": ["B", "C"],       // A,B,C,D,F,M — empty = all categories
      "is_removed": true,             // optional flags
      "is_changed": true,
      "is_new": true,
      "is_verified": true             // manually verified
    }
  ]
}
```

### Sections (7 total)
| ID | Name | Active Qs |
|----|------|-----------|
| osnove_bezbednosti | Основе безбедности саобраћаја и појмови | 169 |
| vozaci | Возачи | 201 |
| vozila | Возила | 361 |
| saobracajna_signalizacija | Саобраћајна сигнализација | 522 |
| pravila_saobracaja | Правила саобраћаја | 794 |
| posebne_mere | Посебне мере и овлашћења | 61 |
| posledice | Последице непоштовања прописа | 180 |

### Vehicle Categories
A (motorcycles), B (cars, DEFAULT), C (trucks), D (buses), F (tractors), M (mopeds)
Questions without categories = for all categories.
Category filtering implemented in getActiveQuestions().

### QuestionCarousel Component
Shared by all 5 modes with configurable props:
```ts
{
  questions: Question[],
  headerTitle: string,
  headerSub?: string,        // enables "section · №id" in header
  showLangToggle?: boolean,  // default true
  showBookmark?: boolean,    // default true
  showFlag?: boolean,        // default true
  showTimer?: boolean,       // default false
  timerSeconds?: number,     // default 2700
  forceLang?: Lang,          // overrides user language
  onBack: () => void,
  onComplete?: () => void,
  score?: number,            // bindable, sum of points
  wrongIds?: string[],       // bindable
}
```

Layout: slide-body (question, flex-shrink:999) + slide-answers (scroll) + footer (position:absolute bottom)

### Exam Rules (Serbian official)
- 41 questions, exactly 100 points total
- Proportional distribution across 7 sections
- 45 minutes
- Pass: ≥80 points (category B) / ≥104 (category C,D)
- Questions forced to Serbian language
- Score = sum of points for correct answers

### SRS Algorithm (learn page)
- Streak tracking: correct→streak+1, wrong→streak=0
- Intervals: [0, 1, 3, 7, 21] days by streak level
- Session priority: 1) due reviews 2) learning 3) new questions
- New questions unlock progressively by section (≥30% of prev section progressed → next unlocks)
- Formula: ~2700 / questions_per_session = days to prepare (at 2 sessions/day)

### Mistakes Logic
- streak=0 → red (last answer wrong)
- streak=1 → orange (recovering, 1 correct after wrong)
- streak≥2 → cleared, removed from mistakes

### Topics System (section 1 only)
12 topics defined in topics.ts with:
- Serbian + Russian names
- Formatted hints (**bold** terms, \n line breaks → rendered as HTML)
- Question ID arrays
- Chunks of ≤20 within each topic

Other 6 sections use flat chunks of 20.

### Verify.py (localhost:8765)
- Two-column: form left, screenshot right (from db_new/)
- Interactive crop tool (drag + Enter)
- AI Parse button (Claude Vision → fills form)
- Real-time word-level diff
- Hotkeys: arrows, digits, Space+Enter (verify & next), Escape
- Russian text editing (text_ru fields)
- Category checkboxes (A,B,C,D,F,M)
- Verified flag with green pills

### Translation Notes
- Latin→Cyrillic post-processing in parse_vision.py and verify.py
- Key terminology: одстојање=дистанция, растојање=боковой интервал
- Known issues: ~35 questions with bad translations (unverified), 7 without answers (unverified)
- Duplicate SR texts normal (239× "Саобраћајни знак приказан на слици означава:" — different images)

### How to Work With This Project

```bash
# Dev server
cd app/ && make dev

# Deploy (syncs data + builds + pushes to gh-pages)
cd app/ && make deploy

# Run verifier
cd database/ && python3 verify.py  # needs ANTHROPIC_API_KEY for AI Parse

# Translate missing
cd database/ && python3 translate.py

# Extract answers from PDF
cd database/ && python3 extract_answers.py
```

### Known Issues / TODO
1. 7 questions without correct answers (unverified)
2. ~35 questions with bad Russian translations (unverified)  
3. 8 questions with uncertain distance/interval translations (unverified)
4. Topics defined only for section 1 — 6 more sections need topics
5. Svelte warning: forceLang initial value capture (cosmetic)
6. SRS learnCount estimate is approximate
7. Category filtering doesn't update exam question count display
8. Service worker not implemented (PWA works online only)
