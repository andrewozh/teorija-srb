# 🚗 Driving Exam App — Feature Spec

## Tech Stack
- **PWA** (Progressive Web App)
- Vanilla HTML/CSS/JS or lightweight framework (Preact/Svelte)
- GitHub Pages hosting
- Service Worker for offline mode
- LocalStorage for progress persistence

## Screens

### 1. Home
Colored cards (like reference screenshot 1):
- **Тренировка** (Practice) — `X / 1780 questions completed`
- **Испит** (Mock Exam) — `X successful attempts`
- **Моје грешке** (My Mistakes) — `X questions to repeat`
- **Статистика** (Statistics) — overall progress

### 2. Practice — Section List
- Toggle: **By Section** / **All Questions**
- 7 sections listed with progress rings:
  - Правила саобраћаја (797)
  - Саобраћајна сигнализација (523)
  - Основе безбедности (100)
  - Возачи (99)
  - Возила (101)
  - Посебне мере (61)
  - Последице (99)
- Each section expandable into chunks of 20 questions
- Progress shown: `X / 20` per chunk, color-coded (gray → in progress → green)

### 3. Question View
Top: horizontal question number pills (1, 2, 3, ... scrollable)
- Current question highlighted
- Answered correctly = green pill
- Answered wrong = red pill
- Not yet answered = gray pill

Center:
- Image (if question has one)
- Question text
- Answer options as tappable cards

Bottom: (after answering)
- Correct answer highlighted green
- Wrong selection highlighted red
- "Next" button or swipe to advance

Header:
- Back button
- Timer (in exam mode)
- Bookmark toggle ⭐
- Font size toggle (Aa)

### 4. Mock Exam
- 41 random questions (matching real exam format)
- 45 minute timer
- Can't go back to previous questions (or can — TBD)
- Results screen at the end:
  - Score: X / 41
  - Pass/Fail (≤ 5 errors = pass)
  - List of wrong answers with correct ones shown
  - Option to review mistakes

### 5. My Mistakes
- List of all questions answered incorrectly
- Grouped by section
- Can re-practice them
- Questions removed from "mistakes" after answered correctly N times (configurable?)

### 6. Statistics
- Overall progress: X% questions practiced
- Per-section breakdown
- Mock exam history (date, score, pass/fail)
- Streak / study days (optional)

### 7. Settings
- **Theme**: Light / Dark / System
- **Font size**: Small / Medium / Large
- **Export progress**: Download JSON file
- **Import progress**: Upload JSON file
- **Reset progress**: With confirmation

## Data Model (LocalStorage)

```json
{
  "version": 1,
  "progress": {
    "pravila_saobracaja": {
      "42": { "correct": 3, "wrong": 1, "last": "2026-04-17" },
      "43": { "correct": 0, "wrong": 2, "last": "2026-04-16" }
    }
  },
  "bookmarks": ["pravila_saobracaja:42", "vozaci:15"],
  "exams": [
    {
      "date": "2026-04-17T14:30:00",
      "score": 37,
      "total": 41,
      "passed": true,
      "wrong_ids": ["pravila_saobracaja:42", "vozila:8", ...]
    }
  ],
  "settings": {
    "theme": "system",
    "fontSize": "medium"
  }
}
```

## Design Guidelines

- **Style**: Clean, minimal, card-based (like reference screenshots)
- **Colors**:
  - Primary: blue (practice), green (exam/correct), red (mistakes/wrong)
  - Cards: colored backgrounds with white text + white icons
  - Questions: white/dark cards, neutral background
- **Typography**: System font stack, Serbian Cyrillic
- **Layout**: Mobile-first, max-width ~480px centered on desktop
- **Animations**: Subtle transitions on card tap, slide between questions
- **Dark mode**: True dark (#1a1a1a background), not just inverted

## Question States

| State | Color | Meaning |
|-------|-------|---------|
| Unanswered | Gray | Not yet attempted |
| Correct | Green | Answered correctly |
| Wrong | Red | Answered incorrectly |
| Bookmarked | ⭐ | Saved for review |
| Removed | Strikethrough | No longer in exam database |

## Offline Behavior

- Service worker caches: HTML, CSS, JS, questions.json, all images
- Full functionality offline after first visit
- Progress stored in LocalStorage (survives offline)
- Export/Import for backup across devices

## Out of Scope (v1)

- User accounts / cloud sync
- Push notifications
- Multiple languages for UI
- Explanation of correct answers (we don't have this data)
- Audio / text-to-speech
