# TODO

- [+] fix paths on gh pages hosting (conflict with main webpage)

**Known Issuess:**

- stole list of big/files + hashsums to verify (instead of files itself in repo)
- why images is in PNG (lets use complessed types)

- fix translation quality
- fix pwa paddings on iphone
- fix question points values (parsed wrong)

**Improvements:**

- group questions by category A B C D ?
- group questions by subcategory in topic
- answers files also contains hints! parse those comments for special questions
- learning assistant (same algorithm for constant repeating questions as ru app)

**Design:**

- good app icon
- navigation gestures (
    gracefully swipe questions left and right
    swiper from left corner for back
  )
- about page (buy-me-a-coffee)

homepage:
  header
  icon
  quick import (if no progress)
  how to export/import guide (if no progress)


header: back, language, page name, menu
question header:
  section > topic > question number, 
  question mark (new changed removed), 
  failed prev [!]
  bookmark button
  report button
questions main block:
  answers always in bottom half to easily reach with thumb
question footer: language, hint
