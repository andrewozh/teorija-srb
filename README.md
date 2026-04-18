# TODO

- [+] fix paths on gh pages hosting (conflict with main webpage)
- [~] fix translation quality
  send question+answers to google translate and compare with current translations
  probably need something even  

**Known Issuess:**

- stole list of big/files + hashsums to verify (instead of files itself in repo)
- why images is in PNG (lets use complessed types)

- fix pwa paddings on iphone
- fix question points values (parsed wrong)

**Improvements:**

- separate app language & questions langiange (if questions language )
- group questions by category A B C D ?
- group questions by subcategory in topic
- answers files also contains hints! parse those comments for special questions
- learning assistant (same algorithm for constant repeating questions as ru app)

# Design

Context: this is PWA application for learning and practicing questions for Serbian driving license exam.

Features:
* minimalistic app icon
* Russian language support
* quick switch between serbian and Russian

Header (page element: available on all pages):
* back button (if needed)
* page name
* settings button

Settings page:
* Language (App language, questions language)
* Theme (light/dark/system)
* Import/export data

Homepage:
* Welcome message (if app data is empty)
  Quick import button
* Link to page: Training
* Link to page: Exam
* Link to page: Mistakes (leads to questions block page)
* Link to page: Statistics
* Link to page: About (at the bottom of page)

Training page:
* Shows the sections with progress bars: leads to section page

Trainig/Section page:
* Contains blocks of questions (20 questions per block) with progress bars: leads to questions block page

Exam page:
* Exam rules
* Exam stats
* Start buttom: leads to questions block page

Questions block page:
* Questions row: a line of numbered links to questions in block (color according to answer)
* Question header: icons for new/changed/removed, section > topic > question number, failed prev question mark
* Question main block: image (if any), question text, answers (the answers must always be at bottom half of screen to be easily reachable with thumb)
* Question footer (minimalistic buttons): language switcher, bookmark button, report button, hint button (if any)
* navigation gestures: gracefully swipe questions left and right

Statistics page:
* todo

About:
* Database updated at
* Question source
* Answers source
* Links
* By me a coffe

