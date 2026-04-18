# TODO

- [+] fix paths on gh pages hosting (conflict with main webpage)
- [+] fix translation quality
  send question+answers to google translate and compare with current translations
  probably need something even better -- Claude

**Known Issuess:**

- stole list of big/files + hashsums to verify (instead of files itself in repo)
- why images is in PNG (lets use complessed types)

- fix pwa paddings on iphone
- fix question points values (parsed wrong)

**Improvements:**

- separate app language & questions langiange (if questions language )
- group questions by category A B C D ? -- already parsed
- group questions by subcategory in topic
- answers files also contains hints! parse those comments for special questions
- learning assistant (same algorithm for constant repeating questions as ru app)

# Design

## What is this

A mobile PWA for studying questions for the Serbian driving license theory exam.
~1780 questions grouped into 9 topic sections. Some questions have images.
Two languages: Serbian Cyrillic (primary) and Russian (secondary).
Works fully offline. All progress stored locally.

## General

- Mobile-first, phone-sized layout
- Minimalistic app icon (car/road/driving theme)
- Light / Dark / System theme
- Clean, minimal aesthetic
- Serbian Cyrillic + Russian language support
- Quick language switch always accessible (one tap, not buried in settings)

## Header (global, all pages)

- Back button (only shown when not on home)
- Page name
- Settings button

## Pages

### Homepage

First visit (no data):
- Welcome message
- Quick import button (restore progress from file)

Normal state — navigation cards:
- Training
- Exam
- Mistakes
- Statistics
- About (at the bottom, less prominent)

### Settings

- Language: separate app language and questions language
- Theme: light / dark / system
- Import / export progress data
- Categorie:
  A	Мотоциклы
  B	Легковые автомобили
  C	Грузовики
  D	Автобусы
  F	Тракторы

### Assisted learning

- Progress stats summary
- Quick setting: how many questions per session
- Start button → opens questions block page
- Algorithm explanation

### Training

List of 9 topic sections with progress indicators. Each section links to its section page.

### Training / Section

Blocks of ~20 questions with progress indicators. Each block links to the questions block page.

### Exam

- Exam rules explanation
- Past exam stats summary
- Start button → opens questions block page in exam mode

### Questions Block (core screen)

This is the most used screen. Needs the most design attention.

**Questions row:** horizontal scrollable line of numbered pills, colored by answer status (unanswered / correct / wrong). Tap to jump to any question.

**Question header:**
- Breadcrumb: section > topic > question number
- Status icons: new question, changed question, removed question
- Warning mark if previously failed

**Question body:**
- Image (if any)
- Question text
- Answer options
- ⚠️ **Answers must always be in the bottom half of the screen** so they're easy to reach with one thumb

**Question footer (minimalistic icon buttons):**
- Language switcher (swap question text between SR and RU)
- Bookmark button
- Report button
- Hint button (only if hint data exists for this question)

**Navigation gestures:** swipe left/right to move between questions. Should feel smooth and natural.

### Statistics

Three sections:

- **Overall progress** — large circular progress ring with percentage, plus three counters: completed, remaining, mistakes
- **Per-section breakdown** — each of the 9 sections with a progress bar and completed/total count
- **Exam history** — list of past exam attempts (newest first), each showing: pass/fail mark, score (e.g. 37/41), date, error count. Empty state message when no exams taken yet.

### About

- Database last updated date
- Question source
- Answer source
- Relevant links
- Buy me a coffee

