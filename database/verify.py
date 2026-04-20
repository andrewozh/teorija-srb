#!/usr/bin/env python3
"""
Question verification/editing web app.
Run: python3 verify.py
Open: http://localhost:8765
"""

import json
import os
import shutil
import io
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
IMAGES_DIR = BASE_DIR / "images"
SECTIONS_FILE = BASE_DIR / "sections.json"
LOG_FILE = BASE_DIR / "verify_log.jsonl"
DB_NEW_DIR = BASE_DIR.parent / "db_new"
PORT = 8765

SECTION_DIR_MAP = {
    "osnove_bezbednosti": "01_osnove_bezbednosti",
    "vozaci": "02_vozaci",
    "vozila": "03_vozila",
    "saobracajna_signalizacija": "04_signalizacija",
    "pravila_saobracaja": "05_pravila_saobracaja",
    "posebne_mere": "06_posebne_mere",
    "posledice": "07_posledice",
}


def log_changes(entry: dict):
    """Append a change entry to the log file."""
    import datetime
    entry["timestamp"] = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_data():
    return json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))


def save_data(data):
    QUESTIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_sections():
    sections = json.loads(SECTIONS_FILE.read_text(encoding="utf-8"))
    return [s for s in sections if s.get("answers_header")]


def find_question(data, section, qid):
    for i, q in enumerate(data["questions"]):
        if q["section"] == section and q["id"] == qid:
            return i, q
    return None, None


def get_section_ids(data, section):
    return sorted(set(q["id"] for q in data["questions"] if q["section"] == section))


def get_max_id(data, section):
    ids = get_section_ids(data, section)
    return max(ids) if ids else 0


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Question Verifier</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, system-ui, sans-serif; background: #f5f5f0; color: #222; font-size: 13px; }

/* === FIXED HEADER === */
.header { position: sticky; top: 0; z-index: 100; background: #f5f5f0; border-bottom: 1px solid #ccc; padding: 6px 12px; }
.header-row { display: flex; gap: 6px; align-items: center; flex-wrap: nowrap; }
.header select, .header input, .header button { padding: 4px 8px; border-radius: 6px; border: 1px solid #ccc; background: #fff; color: #222; font-size: 13px; }
.header select { max-width: 220px; }
.header input[type=number] { width: 64px; }
.header button { cursor: pointer; background: #d4a54a; color: #fff; border: none; font-weight: 600; padding: 4px 10px; }
.header button:hover { background: #b8912e; }
.header .btn-outline { background: #fff; border: 1px solid #ccc; color: #444; }
.header .btn-outline:hover { background: #eee; }
.status { padding: 3px 8px; border-radius: 6px; font-size: 11px; font-family: monospace; white-space: nowrap; }
.status-exists { background: #e8f5e8; color: #2d6a2d; }
.status-missing { background: #f5e8e8; color: #aa3333; }
.status-empty { background: #f5f0e0; color: #8b6914; }

/* === FILTERS === */
.filters-bar { padding: 4px 12px; display: flex; gap: 4px; flex-wrap: wrap; align-items: center; font-size: 11px; }
.filters-bar a { padding: 2px 8px; border-radius: 999px; font-size: 11px; font-family: monospace; text-decoration: none; border: 1px solid #ccc; color: #555; background: #fff; }
.filters-bar a:hover { background: #eee; }
.filters-bar a.active { background: #d4a54a; color: #fff; border-color: #d4a54a; }
.filters-bar a.f-changed { border-color: #c9960a; color: #8b6914; }
.filters-bar a.f-changed.active { background: #d4a54a; color: #fff; }
.filters-bar a.f-removed { border-color: #cc4444; color: #aa3333; }
.filters-bar a.f-removed.active { background: #cc4444; color: #fff; }
.filters-bar a.f-new { border-color: #44aa44; color: #338833; }
.filters-bar a.f-new.active { background: #44aa44; color: #fff; }
.filters-bar a.f-problems { border-color: #cc6600; color: #aa5500; }
.filters-bar a.f-problems.active { background: #cc6600; color: #fff; }

/* === ID GRID (pills) === */
.id-grid { display: flex; flex-wrap: wrap; gap: 2px; padding: 4px 12px 4px; }
.id-btn { width: 30px; height: 24px; border-radius: 4px; border: 1px solid #ddd; background: #fff; color: #888; font-size: 10px; font-family: monospace; cursor: pointer; display: flex; align-items: center; justify-content: center; text-decoration: none; }
.id-btn:hover { background: #eee; }
.id-btn.exists { color: #2d6a2d; border-color: #5c7a48; }
.id-btn.current { background: #d4a54a; color: #fff; border-color: #d4a54a; font-weight: 700; }
.id-btn.missing { color: #aa3333; border-color: #cc4444; }

/* === TWO-COLUMN LAYOUT === */
.main { display: flex; gap: 0; padding: 0; }
.col-left { flex: 1; min-width: 0; padding: 8px 12px; overflow-y: auto; }
.col-right { width: 50%; min-width: 380px; padding: 8px 12px; position: sticky; top: 80px; align-self: flex-start; max-height: calc(100vh - 90px); overflow-y: auto; }
.col-right img { width: 100%; border-radius: 6px; border: 1px solid #ddd; }
.col-right .no-screenshot { color: #999; font-size: 12px; font-family: monospace; padding: 20px; text-align: center; background: #fafafa; border-radius: 6px; border: 1px dashed #ccc; }

/* === CARDS === */
.card { background: #fff; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; border: 1px solid #ddd; }
.card h3 { font-size: 11px; color: #888; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; font-family: monospace; }
.field { margin-bottom: 8px; }
.field label { display: block; font-size: 11px; color: #888; margin-bottom: 2px; font-family: monospace; text-transform: uppercase; }
.field textarea, .field input[type=text], .field input[type=number], .field select { width: 100%; padding: 5px 8px; border-radius: 4px; border: 1px solid #ccc; background: #fafafa; color: #222; font-size: 13px; font-family: inherit; }
.field textarea { min-height: 40px; resize: none; overflow: hidden; }

/* === COMPACT NUMERIC ROW === */
.num-row { display: flex; gap: 12px; }
.num-row .field { flex: 0 0 auto; }
.num-row .field input[type=number] { width: 64px; }

/* === OPTIONS === */
.option-row { display: flex; gap: 6px; align-items: center; margin-bottom: 4px; padding: 5px 8px; border-radius: 6px; background: #fafafa; border: 1px solid #ddd; }
.option-row.correct { border-color: #5c7a48; background: #f0f7ec; }
.option-letter { font-weight: 700; font-size: 14px; width: 20px; text-align: center; flex-shrink: 0; }
.option-text { flex: 1; min-width: 0; }
.option-text input { width: 100%; padding: 4px 6px; border-radius: 4px; border: 1px solid #ccc; background: #fff; color: #222; font-size: 13px; }
.option-correct { cursor: pointer; flex-shrink: 0; }
.option-correct input { cursor: pointer; width: 16px; height: 16px; }

/* === FLAGS === */
.flags-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.flag { padding: 2px 8px; border-radius: 999px; font-size: 10px; font-family: monospace; }
.flag-removed { background: #fce8e8; color: #aa3333; }
.flag-changed { background: #fdf3dc; color: #8b6914; }
.flag-new { background: #e8f5e8; color: #338833; }

/* === IMAGE UPLOAD === */
.upload-row { display: flex; gap: 8px; align-items: center; }
.upload-row label { font-size: 11px; color: #888; font-family: monospace; text-transform: uppercase; white-space: nowrap; }
.img-preview { max-width: 100%; max-height: 120px; border-radius: 6px; margin: 4px 0; }

/* === SAVE BAR === */
.save-bar { position: sticky; bottom: 0; background: #f5f5f0; padding: 8px 12px; border-top: 1px solid #ddd; display: flex; gap: 8px; justify-content: flex-end; z-index: 50; }
.save-bar button { padding: 8px 20px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.save-bar .btn-save { background: #2d6a2d; color: white; }
.save-bar .btn-save:hover { background: #3d8a3d; }

/* === MESSAGES === */
.msg { padding: 6px 12px; border-radius: 6px; margin: 4px 12px; font-size: 12px; }
.msg-ok { background: #e8f5e8; color: #2d6a2d; }
.msg-err { background: #fce8e8; color: #aa3333; }

/* === META === */
.meta-row { display: flex; gap: 12px; flex-wrap: wrap; }
.meta-item { font-size: 11px; color: #888; font-family: monospace; }
</style>
</head>
<body>

<!-- FIXED HEADER -->
<div class="header">
<form method="GET" action="/" id="navform">
<div class="header-row">
    <select name="section" onchange="this.form.submit()">
        {section_options}
    </select>
    <input type="number" name="id" value="{current_id}" min="1" placeholder="ID">
    <button type="submit">Go</button>
    <button type="button" class="btn-outline" onclick="go({prev_id})">←</button>
    <button type="button" class="btn-outline" onclick="go({next_id})">→</button>
    <span class="{status_class}">{status_text}</span>
</div>
</form>
<div class="filters-bar">
    {filter_buttons}
</div>
</div>

{message}

<div class="id-grid">{id_grid}</div>

<!-- TWO-COLUMN LAYOUT -->
<form method="POST" action="/save" enctype="multipart/form-data" id="editform">
<input type="hidden" name="section" value="{current_section}">
<input type="hidden" name="original_id" value="{current_id}">

<div class="main">
    <div class="col-left">
        {question_form}
        <div class="save-bar">
            <button type="submit" class="btn-save">💾 Save</button>
        </div>
    </div>
    <div class="col-right">
        {screenshot_html}
    </div>
</div>
</form>

<script>
function go(id) {
    const section = document.querySelector('select[name=section]').value;
    const params = new URLSearchParams(window.location.search);
    const filter = params.get('filter');
    let url = '/?section=' + section + '&id=' + id;
    if (filter) url += '&filter=' + filter;
    window.location = url;
}

// Auto-expand textareas
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = el.scrollHeight + 'px';
}
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('textarea').forEach(function(ta) {
        autoResize(ta);
        ta.addEventListener('input', function() { autoResize(this); });
    });
});
</script>
</body>
</html>"""


def render_question_form(q, section, qid):
    if q is None:
        return f"""
        <div class="card">
            <h3>Question {qid} — NOT PARSED</h3>
            <p style="color:#c9715c;margin-bottom:8px;font-size:12px;">Not found in database. Fill in to create.</p>
            <div class="field">
                <label>Text</label>
                <textarea name="text" placeholder="Question text..."></textarea>
            </div>
            <div class="num-row">
                <div class="field">
                    <label>Points</label>
                    <input type="number" name="points" value="2" min="1" max="4">
                </div>
                <div class="field">
                    <label>Correct count</label>
                    <input type="number" name="correct_answers_count" value="1" min="1" max="5">
                </div>
            </div>
            <div class="upload-row">
                <label>Image</label>
                <input type="file" name="image" accept="image/*" style="font-size:12px;">
            </div>
            <div class="field" style="margin-top:8px;">
                <label>Options (letter|text|correct — e.g. а|правилом саобраћаја|false)</label>
                <textarea name="options_raw" rows="5" placeholder="а|text|false&#10;б|text|true&#10;в|text|false" style="min-height:80px;resize:vertical;"></textarea>
            </div>
        </div>"""

    # Existing question
    img_html = ""
    if q.get("image"):
        img_path = f"/image/{q['image']}"
        img_html = f'<img src="{img_path}" class="img-preview" alt="Question image">'

    options_html = ""
    correct_answers = set(q.get("correct_answers", []))
    for i, o in enumerate(q["options"]):
        is_correct = o["letter"] in correct_answers
        cls = "correct" if is_correct else ""
        checked = "checked" if is_correct else ""
        options_html += f"""
        <div class="option-row {cls}">
            <span class="option-letter">{o['letter']})</span>
            <div class="option-text">
                <input type="text" name="opt_{i}_text" value="{o['text']}">
            </div>
            <div class="option-correct" title="Correct answer">
                <input type="checkbox" name="opt_{i}_correct" {checked}>
            </div>
            <label style="font-size:10px;color:#aa3333;cursor:pointer;display:flex;align-items:center;gap:2px;" title="Delete">
                <input type="checkbox" name="opt_{i}_delete"> ✕
            </label>
            <input type="hidden" name="opt_{i}_letter" value="{o['letter']}">
        </div>"""

    cats = ", ".join(q.get("categories", [])) or "все"

    # Flag checkboxes
    chk_removed = "checked" if q.get("is_removed") else ""
    chk_changed = "checked" if q.get("is_changed") else ""
    chk_new = "checked" if q.get("is_new") else ""

    return f"""
    <div class="card">
        <h3>Q{q['id']} — {section}</h3>
        <div class="meta-row" style="margin-bottom:6px;">
            <span class="meta-item">pts: {q['points']}</span>
            <span class="meta-item">correct: {q['correct_answers_count']}</span>
            <span class="meta-item">cats: {cats}</span>
            <span class="meta-item">img: {q['has_image']}</span>
        </div>
        <div class="flags-row">
            <label style="font-size:12px;display:flex;align-items:center;gap:3px;">
                <input type="checkbox" name="flag_removed" {chk_removed}> <span class="flag flag-removed">removed</span>
            </label>
            <label style="font-size:12px;display:flex;align-items:center;gap:3px;">
                <input type="checkbox" name="flag_changed" {chk_changed}> <span class="flag flag-changed">changed</span>
            </label>
            <label style="font-size:12px;display:flex;align-items:center;gap:3px;">
                <input type="checkbox" name="flag_new" {chk_new}> <span class="flag flag-new">new</span>
            </label>
        </div>
    </div>

    <div class="card">
        <h3>Text</h3>
        <div class="field">
            <textarea name="text">{q['text']}</textarea>
        </div>
        <div class="num-row">
            <div class="field">
                <label>Points</label>
                <input type="number" name="points" value="{q['points']}" min="1" max="4">
            </div>
            <div class="field">
                <label>Correct count</label>
                <input type="number" name="correct_answers_count" value="{q['correct_answers_count']}" min="1" max="6">
            </div>
        </div>
    </div>

    <div class="card">
        <h3>Image</h3>
        {img_html}
        <div class="upload-row">
            <label>Upload</label>
            <input type="file" name="image" accept="image/*" style="font-size:12px;">
        </div>
    </div>

    <div class="card">
        <h3>Options <span style="font-size:10px;color:#888;font-weight:400;">(✓ = correct, ✕ = delete)</span></h3>
        <input type="hidden" name="options_count" value="{len(q['options'])}">
        {options_html}
        <div style="margin-top:8px;padding-top:8px;border-top:1px solid #ddd;">
            <div style="font-size:10px;color:#888;margin-bottom:4px;font-family:monospace;">ADD OPTION</div>
            <div style="display:flex;gap:6px;align-items:center;">
                <input type="text" name="new_opt_letter" placeholder="е" style="width:36px;padding:4px;border-radius:4px;border:1px solid #ccc;text-align:center;font-size:13px;">
                <input type="text" name="new_opt_text" placeholder="Текст варианта..." style="flex:1;padding:4px 6px;border-radius:4px;border:1px solid #ccc;font-size:13px;">
                <label style="font-size:11px;display:flex;align-items:center;gap:2px;white-space:nowrap;">
                    <input type="checkbox" name="new_opt_correct"> ✓
                </label>
            </div>
        </div>
    </div>"""


class VerifyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        # Serve question images from database/images
        if parsed.path == "/image/" or parsed.path.startswith("/image/"):
            filename = parsed.path.replace("/image/", "")
            filepath = IMAGES_DIR / filename
            if filepath.exists():
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                self.wfile.write(filepath.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
            return

        # Serve screenshots from db_new
        if parsed.path.startswith("/screenshot/"):
            # /screenshot/<section>/<qNNN>.png
            parts = parsed.path.split("/")
            if len(parts) >= 4:
                section_id = parts[2]
                filename = parts[3]
                dir_name = SECTION_DIR_MAP.get(section_id, "")
                if dir_name:
                    filepath = DB_NEW_DIR / dir_name / filename
                    if filepath.exists():
                        ct = "image/png"
                        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
                            ct = "image/jpeg"
                        self.send_response(200)
                        self.send_header("Content-Type", ct)
                        self.end_headers()
                        self.wfile.write(filepath.read_bytes())
                        return
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        data = load_data()
        sections = get_sections()

        section = params.get("section", [sections[0]["id"]])[0]
        qid = int(params.get("id", ["1"])[0])
        msg = params.get("msg", [""])[0]

        filter_type = params.get("filter", [""])[0]

        section_ids = get_section_ids(data, section)
        max_id = max(section_ids) if section_ids else 1
        all_ids = set(range(1, max_id + 1))

        # Build filtered ID list based on filter
        section_questions = {q["id"]: q for q in data["questions"] if q["section"] == section}

        def _is_problem(q):
            opts = q.get("options", [])
            text = q.get("text", "")
            if len(opts) < 2: return True
            if len(text) < 10: return True
            letters = [o["letter"] for o in opts]
            if len(letters) != len(set(letters)): return True
            if len(opts) > 6: return True
            if any("СРБИЈА" in o["text"] or "ПОЛИЦИЈЕ" in o["text"] for o in opts): return True
            if "correct_answers" in q and not q.get("is_removed") and q["correct_answers_count"] != len(q.get("correct_answers", [])): return True
            if "correct_answers" in q and any(c not in {o["letter"] for o in opts} for c in q["correct_answers"]): return True
            return False

        def _is_garbled(q):
            text = q.get("text", "")
            if not text: return True
            words = text.split()
            if len(words) > 3 and sum(1 for w in words if len(w) == 1 and w.isalpha()) > len(words) * 0.25: return True
            if len(text) > 20 and text.count(" ") / len(text) > 0.35: return True
            for w in words:
                if len(w) > 3 and text.count(w) > 2: return True
            for o in q.get("options", []):
                ot = o.get("text", "")
                if "СРБИЈА" in ot or "ПОЛИЦИЈЕ" in ot: return True
                owords = ot.split()
                if len(owords) > 2 and sum(1 for w in owords if len(w) == 1 and w.isalpha()) > len(owords) * 0.3: return True
            return False
        if filter_type == "changed":
            filtered_ids = sorted(qid for qid, q in section_questions.items() if q.get("is_changed"))
        elif filter_type == "removed":
            filtered_ids = sorted(qid for qid, q in section_questions.items() if q.get("is_removed"))
        elif filter_type == "new":
            filtered_ids = sorted(qid for qid, q in section_questions.items() if q.get("is_new"))
        elif filter_type == "problems":
            filtered_ids = sorted(qid for qid, q in section_questions.items() if _is_problem(q))
        elif filter_type == "garbled":
            filtered_ids = sorted(qid for qid, q in section_questions.items() if _is_garbled(q))
        elif filter_type == "missing":
            filtered_ids = sorted(all_ids - set(section_ids))
        elif filter_type == "no_answer":
            filtered_ids = sorted(qid for qid, q in section_questions.items()
                if "correct_answers" not in q and not q.get("is_removed"))
        else:
            filtered_ids = None

        # Count for filter badges
        n_changed = sum(1 for q in section_questions.values() if q.get("is_changed"))
        n_removed = sum(1 for q in section_questions.values() if q.get("is_removed"))
        n_new = sum(1 for q in section_questions.values() if q.get("is_new"))
        n_problems = sum(1 for q in section_questions.values() if _is_problem(q))
        n_garbled = sum(1 for q in section_questions.values() if _is_garbled(q))
        n_missing = len(all_ids - set(section_ids))
        n_no_answer = sum(1 for q in section_questions.values()
            if "correct_answers" not in q and not q.get("is_removed"))

        _, q = find_question(data, section, qid)

        # Status
        if q:
            if len(q.get("options", [])) < 2 or len(q.get("text", "")) < 5:
                status_class = "status status-empty"
                status_text = f"Q{qid} — incomplete"
            else:
                status_class = "status status-exists"
                status_text = f"Q{qid} — OK ({len(q['options'])} opts)"
        else:
            status_class = "status status-missing"
            status_text = f"Q{qid} — NOT IN DB"

        # Navigation — respects filter
        if filtered_ids:
            cur_pos = filtered_ids.index(qid) if qid in filtered_ids else -1
            prev_id = filtered_ids[cur_pos - 1] if cur_pos > 0 else filtered_ids[0]
            next_id = filtered_ids[cur_pos + 1] if cur_pos >= 0 and cur_pos < len(filtered_ids) - 1 else filtered_ids[-1]
        else:
            prev_id = max(1, qid - 1)
            next_id = min(max_id + 1, qid + 1)

        # Section options
        section_options = ""
        for s in sections:
            sel = "selected" if s["id"] == section else ""
            count = len([q2 for q2 in data["questions"] if q2["section"] == s["id"]])
            section_options += f'<option value="{s["id"]}" {sel}>{s["name"]} ({count})</option>'

        # Filter buttons
        filter_base = f"/?section={section}"
        def fbtn(name, label, count, css_class=""):
            active = "active" if filter_type == name else ""
            href = filter_base if filter_type == name else f"{filter_base}&filter={name}&id={qid}"
            return f'<a href="{href}" class="{css_class} {active}">{label} ({count})</a>' if count else ""

        filter_buttons = (
            fbtn("", "All", len(section_ids)) +
            fbtn("changed", "Changed", n_changed, "f-changed") +
            fbtn("new", "New", n_new, "f-new") +
            fbtn("removed", "Removed", n_removed, "f-removed") +
            fbtn("problems", "Problems", n_problems, "f-problems") +
            fbtn("garbled", "Garbled", n_garbled, "f-problems") +
            fbtn("missing", "Missing IDs", n_missing, "f-removed") +
            fbtn("no_answer", "No answer", n_no_answer, "f-problems")
        )

        # ID grid — show filtered IDs or 50 around current
        if filtered_ids:
            grid_ids = filtered_ids
        else:
            grid_start = max(1, qid - 25)
            grid_end = min(max_id + 1, grid_start + 50)
            grid_ids = list(range(grid_start, grid_end + 1))

        id_grid = ""
        filter_param = f"&filter={filter_type}" if filter_type else ""
        for i in grid_ids:
            if i in section_ids:
                cls = "id-btn exists"
            else:
                cls = "id-btn missing"
            if i == qid:
                cls += " current"
            id_grid += f'<a href="/?section={section}&id={i}{filter_param}" class="{cls}">{i}</a>'

        # Message
        message = ""
        if msg == "saved":
            message = '<div class="msg msg-ok">✓ Saved successfully</div>'
        elif msg == "error":
            message = '<div class="msg msg-err">✗ Error saving</div>'

        question_form = render_question_form(q, section, qid)

        # Screenshot HTML
        screenshot_filename = f"q{qid:03d}.png"
        screenshot_url = f"/screenshot/{section}/{screenshot_filename}"
        # Check if file exists
        dir_name = SECTION_DIR_MAP.get(section, "")
        screenshot_exists = False
        if dir_name:
            screenshot_path = DB_NEW_DIR / dir_name / screenshot_filename
            screenshot_exists = screenshot_path.exists()

        if screenshot_exists:
            screenshot_html = f'<img src="{screenshot_url}" alt="Screenshot Q{qid}">'
        else:
            screenshot_html = f'<div class="no-screenshot">No screenshot for Q{qid}<br><span style="font-size:10px;">{screenshot_filename}</span></div>'

        html = HTML_TEMPLATE.replace(
            "{section_options}", section_options
        ).replace(
            "{current_id}", str(qid)
        ).replace(
            "{current_section}", section
        ).replace(
            "{prev_id}", str(prev_id)
        ).replace(
            "{next_id}", str(next_id)
        ).replace(
            "{status_class}", status_class
        ).replace(
            "{status_text}", status_text
        ).replace(
            "{question_form}", question_form
        ).replace(
            "{id_grid}", id_grid
        ).replace(
            "{filter_buttons}", filter_buttons
        ).replace(
            "{message}", message
        ).replace(
            "{screenshot_html}", screenshot_html
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def parse_multipart(self):
        """Parse multipart/form-data without cgi module."""
        content_type = self.headers.get("Content-Type", "")
        boundary = content_type.split("boundary=")[-1].encode()
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        parts = body.split(b"--" + boundary)
        fields = {}
        files = {}
        
        for part in parts:
            if b"Content-Disposition" not in part:
                continue
            header_end = part.find(b"\r\n\r\n")
            if header_end < 0:
                continue
            header = part[:header_end].decode("utf-8", errors="replace")
            content = part[header_end + 4:]
            if content.endswith(b"\r\n"):
                content = content[:-2]
            
            # Extract name
            name = ""
            if 'name="' in header:
                name = header.split('name="')[1].split('"')[0]
            
            # Check if file
            if 'filename="' in header:
                filename = header.split('filename="')[1].split('"')[0]
                if filename:
                    files[name] = {"filename": filename, "data": content}
            else:
                fields[name] = content.decode("utf-8", errors="replace")
        
        return fields, files

    def do_POST(self):
        fields, files = self.parse_multipart()

        section = fields.get("section", "")
        original_id = int(fields.get("original_id", "0"))
        text = fields.get("text", "").strip()
        text_ru = fields.get("text_ru", "").strip()
        points = int(fields.get("points", "2"))
        correct_count = int(fields.get("correct_answers_count", "1"))

        data = load_data()
        idx, q = find_question(data, section, original_id)

        # Handle image upload
        image_filename = ""
        if "image" in files:
            ext = Path(files["image"]["filename"]).suffix or ".png"
            image_filename = f"verify_{section}_{original_id}{ext}"
            img_path = IMAGES_DIR / image_filename
            IMAGES_DIR.mkdir(exist_ok=True)
            with open(img_path, "wb") as f:
                f.write(files["image"]["data"])

        changes = []

        if q is None:
            # Create new question
            q = {
                "id": original_id,
                "section": section,
                "text": text,
                "options": [],
                "points": points,
                "correct_answers_count": correct_count,
                "has_image": bool(image_filename),
            }
            if image_filename:
                q["image"] = image_filename

            # Parse options from raw text
            raw = fields.get("options_raw", "")
            if raw:
                correct_answers = []
                for line in raw.strip().split("\n"):
                    parts = line.strip().split("|")
                    if len(parts) >= 2:
                        letter = parts[0].strip()
                        opt_text = parts[1].strip()
                        is_correct = len(parts) > 2 and parts[2].strip().lower() == "true"
                        q["options"].append({"letter": letter, "text": opt_text})
                        if is_correct:
                            correct_answers.append(letter)
                if correct_answers:
                    q["correct_answers"] = sorted(correct_answers)

            data["questions"].append(q)
            changes.append({"action": "created", "options": len(q["options"])})
        else:
            # Update existing — track all changes
            if q["text"] != text:
                changes.append({"action": "text_changed", "from": q["text"][:80], "to": text[:80]})
                q["text"] = text

            if q["points"] != points:
                changes.append({"action": "points_changed", "from": q["points"], "to": points})
                q["points"] = points

            if q["correct_answers_count"] != correct_count:
                changes.append({"action": "correct_count_changed", "from": q["correct_answers_count"], "to": correct_count})
                q["correct_answers_count"] = correct_count

            if image_filename:
                changes.append({"action": "image_uploaded", "file": image_filename})
                q["image"] = image_filename
                q["has_image"] = True

            # Flags
            for flag_name, field_name in [("is_removed", "flag_removed"), ("is_changed", "flag_changed"), ("is_new", "flag_new")]:
                was_set = q.get(flag_name, False)
                now_set = field_name in fields
                if was_set != now_set:
                    changes.append({"action": "flag_changed", "flag": flag_name, "from": was_set, "to": now_set})
                if now_set:
                    q[flag_name] = True
                else:
                    q.pop(flag_name, None)

            # Options — rebuild, track deletions and changes
            opt_count = int(fields.get("options_count", "0"))
            new_options = []
            correct_answers = []
            for i in range(opt_count):
                old_opt = q["options"][i] if i < len(q["options"]) else {}
                letter = fields.get(f"opt_{i}_letter", old_opt.get("letter", ""))
                old_text = old_opt.get("text", "")

                if f"opt_{i}_delete" in fields:
                    changes.append({"action": "option_deleted", "position": i, "letter": letter, "text": old_text[:60]})
                    continue

                opt_text = fields.get(f"opt_{i}_text", "")
                is_correct = f"opt_{i}_correct" in fields

                if opt_text != old_text:
                    changes.append({"action": "option_text_changed", "position": i, "letter": letter, "from": old_text[:60], "to": opt_text[:60]})

                new_opt = {**old_opt, "letter": letter, "text": opt_text}
                new_options.append(new_opt)

                if is_correct:
                    correct_answers.append(letter)

            # Add new option if provided
            new_letter = fields.get("new_opt_letter", "").strip()
            new_text = fields.get("new_opt_text", "").strip()
            if new_letter and new_text:
                new_opt = {"letter": new_letter, "text": new_text}
                new_options.append(new_opt)
                changes.append({"action": "option_added", "letter": new_letter, "text": new_text[:60]})
                if "new_opt_correct" in fields:
                    correct_answers.append(new_letter)

            q["options"] = new_options

            old_answers = q.get("correct_answers", [])
            new_answers = sorted(correct_answers) if correct_answers else old_answers
            if old_answers != new_answers:
                changes.append({"action": "answers_changed", "from": old_answers, "to": new_answers})
            q["correct_answers"] = new_answers

        # Log
        if changes:
            log_changes({
                "section": section,
                "question_id": original_id,
                "changes": changes,
            })

        save_data(data)

        self.send_response(303)
        self.send_header("Location", f"/?section={section}&id={original_id}&msg=saved")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet


def main():
    print(f"Starting verifier at http://localhost:{PORT}")
    print(f"Database: {QUESTIONS_FILE}")
    print(f"Images: {IMAGES_DIR}")
    print(f"Screenshots: {DB_NEW_DIR}")
    server = HTTPServer(("", PORT), VerifyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
