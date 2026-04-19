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
PORT = 8765


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
body { font-family: -apple-system, system-ui, sans-serif; background: #1a1a1e; color: #e8e8e8; padding: 20px; max-width: 800px; margin: 0 auto; }
h1 { font-size: 20px; margin-bottom: 16px; color: #d4a54a; }
.nav { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }
.nav select, .nav input, .nav button { padding: 8px 12px; border-radius: 8px; border: 1px solid #333; background: #222; color: #e8e8e8; font-size: 14px; }
.nav button { cursor: pointer; background: #d4a54a; color: #1a1a1e; border: none; font-weight: 600; }
.nav button:hover { background: #e8c77a; }
.nav .btn-outline { background: transparent; border: 1px solid #444; color: #e8e8e8; }
.nav .btn-outline:hover { background: #333; }
.nav .btn-danger { background: #b14f38; color: white; }
.status { padding: 8px 12px; border-radius: 8px; font-size: 12px; font-family: monospace; }
.status-exists { background: #1a2e1a; color: #8aa876; }
.status-missing { background: #2e1a1a; color: #c9715c; }
.status-empty { background: #2e2a1a; color: #d4a54a; }
.card { background: #222; border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #333; }
.card h3 { font-size: 14px; color: #888; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; font-family: monospace; }
.field { margin-bottom: 12px; }
.field label { display: block; font-size: 12px; color: #888; margin-bottom: 4px; font-family: monospace; text-transform: uppercase; }
.field textarea, .field input[type=text], .field input[type=number], .field select { width: 100%; padding: 8px 10px; border-radius: 6px; border: 1px solid #444; background: #1a1a1e; color: #e8e8e8; font-size: 14px; font-family: inherit; resize: vertical; }
.field textarea { min-height: 60px; }
.option-row { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; padding: 8px; border-radius: 8px; background: #1a1a1e; border: 1px solid #333; }
.option-row.correct { border-color: #5c7a48; background: rgba(138,168,118,0.08); }
.option-letter { font-weight: 700; font-size: 16px; width: 24px; text-align: center; flex-shrink: 0; }
.option-text { flex: 1; }
.option-text input { width: 100%; padding: 6px 8px; border-radius: 4px; border: 1px solid #444; background: #222; color: #e8e8e8; font-size: 13px; }
.option-correct { cursor: pointer; }
.option-correct input { cursor: pointer; width: 18px; height: 18px; }
.option-actions button { padding: 4px 8px; border-radius: 4px; border: 1px solid #444; background: transparent; color: #888; cursor: pointer; font-size: 11px; }
.option-actions button:hover { background: #333; }
.img-preview { max-width: 100%; border-radius: 8px; margin: 8px 0; }
.flags { display: flex; gap: 8px; flex-wrap: wrap; }
.flag { padding: 4px 10px; border-radius: 999px; font-size: 11px; font-family: monospace; }
.flag-removed { background: rgba(177,79,56,0.2); color: #c9715c; }
.flag-changed { background: rgba(212,165,74,0.2); color: #d4a54a; }
.flag-new { background: rgba(138,168,118,0.2); color: #8aa876; }
.meta-row { display: flex; gap: 16px; flex-wrap: wrap; }
.meta-item { font-size: 12px; color: #888; font-family: monospace; }
.save-bar { position: sticky; bottom: 0; background: #1a1a1e; padding: 12px 0; border-top: 1px solid #333; display: flex; gap: 8px; justify-content: flex-end; }
.save-bar button { padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; }
.save-bar .btn-save { background: #5c7a48; color: white; }
.save-bar .btn-save:hover { background: #8aa876; }
.msg { padding: 10px; border-radius: 8px; margin-bottom: 12px; font-size: 13px; }
.msg-ok { background: rgba(138,168,118,0.15); color: #8aa876; }
.msg-err { background: rgba(177,79,56,0.15); color: #c9715c; }
.id-grid { display: flex; flex-wrap: wrap; gap: 4px; margin: 12px 0; }
.id-btn { width: 40px; height: 30px; border-radius: 6px; border: 1px solid #333; background: #222; color: #888; font-size: 11px; font-family: monospace; cursor: pointer; display: flex; align-items: center; justify-content: center; text-decoration: none; }
.id-btn:hover { background: #333; }
.id-btn.exists { color: #8aa876; border-color: #5c7a48; }
.id-btn.current { background: #d4a54a; color: #1a1a1e; border-color: #d4a54a; font-weight: 700; }
.id-btn.missing { color: #c9715c; border-color: #b14f38; }
</style>
</head>
<body>
<h1>🔍 Question Verifier</h1>
{message}
<form method="GET" action="/">
<div class="nav">
    <select name="section" onchange="this.form.submit()">
        {section_options}
    </select>
    <input type="number" name="id" value="{current_id}" min="1" style="width:80px" placeholder="ID">
    <button type="submit">Go</button>
    <button type="button" class="btn-outline" onclick="go({prev_id})">← Prev</button>
    <button type="button" class="btn-outline" onclick="go({next_id})">Next →</button>
    <span class="{status_class}">{status_text}</span>
</div>
</form>

<div class="id-grid">{id_grid}</div>

<form method="POST" action="/save" enctype="multipart/form-data">
<input type="hidden" name="section" value="{current_section}">
<input type="hidden" name="original_id" value="{current_id}">

{question_form}

<div class="save-bar">
    <button type="submit" class="btn-save">💾 Save</button>
</div>
</form>

<script>
function go(id) {
    const section = document.querySelector('select[name=section]').value;
    window.location = '/?section=' + section + '&id=' + id;
}
</script>
</body>
</html>"""


def render_question_form(q, section, qid):
    if q is None:
        return f"""
        <div class="card">
            <h3>Question {qid} — NOT PARSED</h3>
            <p style="color:#c9715c;margin-bottom:12px;">This question was not found in the database. Fill in to create it.</p>
            <div class="field">
                <label>Text</label>
                <textarea name="text" placeholder="Question text..."></textarea>
            </div>
            <div class="field">
                <label>Points</label>
                <input type="number" name="points" value="2" min="1" max="3">
            </div>
            <div class="field">
                <label>Correct answers count</label>
                <input type="number" name="correct_answers_count" value="1" min="1" max="5">
            </div>
            <div class="field">
                <label>Image</label>
                <input type="file" name="image" accept="image/*">
            </div>
            <div class="field">
                <label>Options (one per line: letter|text|correct — e.g. а|правилом саобраћаја|false)</label>
                <textarea name="options_raw" rows="5" placeholder="а|text|false&#10;б|text|true&#10;в|text|false"></textarea>
            </div>
        </div>"""

    # Existing question
    flags_html = ""
    if q.get("is_removed"):
        flags_html += '<span class="flag flag-removed">REMOVED</span>'
    if q.get("is_changed"):
        flags_html += '<span class="flag flag-changed">CHANGED</span>'
    if q.get("is_new"):
        flags_html += '<span class="flag flag-new">NEW</span>'

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
        text_ru = o.get("text_ru", "")
        options_html += f"""
        <div class="option-row {cls}">
            <span class="option-letter">{o['letter']})</span>
            <div class="option-text">
                <input type="text" name="opt_{i}_text" value="{o['text']}">
                <input type="text" name="opt_{i}_text_ru" value="{text_ru}" placeholder="RU перевод" style="margin-top:4px;color:#888;">
            </div>
            <div class="option-correct">
                <input type="checkbox" name="opt_{i}_correct" {checked}>
            </div>
            <input type="hidden" name="opt_{i}_letter" value="{o['letter']}">
        </div>"""

    cats = ", ".join(q.get("categories", [])) or "все"
    text_ru = q.get("text_ru", "")

    return f"""
    <div class="card">
        <h3>Question {q['id']} — {section}</h3>
        <div class="flags" style="margin-bottom:12px;">{flags_html}</div>
        <div class="meta-row" style="margin-bottom:12px;">
            <span class="meta-item">points: {q['points']}</span>
            <span class="meta-item">correct_count: {q['correct_answers_count']}</span>
            <span class="meta-item">categories: {cats}</span>
            <span class="meta-item">has_image: {q['has_image']}</span>
        </div>
    </div>

    <div class="card">
        <h3>Text</h3>
        <div class="field">
            <label>Serbian</label>
            <textarea name="text">{q['text']}</textarea>
        </div>
        <div class="field">
            <label>Russian</label>
            <textarea name="text_ru">{text_ru}</textarea>
        </div>
        <div class="field">
            <label>Points</label>
            <input type="number" name="points" value="{q['points']}" min="1" max="3">
        </div>
        <div class="field">
            <label>Correct answers count</label>
            <input type="number" name="correct_answers_count" value="{q['correct_answers_count']}" min="1" max="6">
        </div>
    </div>

    <div class="card">
        <h3>Image</h3>
        {img_html}
        <div class="field">
            <label>Upload new image</label>
            <input type="file" name="image" accept="image/*">
        </div>
    </div>

    <div class="card">
        <h3>Options</h3>
        <input type="hidden" name="options_count" value="{len(q['options'])}">
        {options_html}
    </div>"""


class VerifyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

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

        params = parse_qs(parsed.query)
        data = load_data()
        sections = get_sections()

        section = params.get("section", [sections[0]["id"]])[0]
        qid = int(params.get("id", ["1"])[0])
        msg = params.get("msg", [""])[0]

        section_ids = get_section_ids(data, section)
        max_id = max(section_ids) if section_ids else 1
        all_ids = set(range(1, max_id + 1))

        _, q = find_question(data, section, qid)

        # Status
        if q:
            if len(q.get("options", [])) < 2 or len(q.get("text", "")) < 5:
                status_class = "status status-empty"
                status_text = f"Q{qid} — parsed but incomplete"
            else:
                status_class = "status status-exists"
                status_text = f"Q{qid} — OK ({len(q['options'])} options)"
        else:
            status_class = "status status-missing"
            status_text = f"Q{qid} — NOT IN DATABASE"

        # Navigation
        prev_id = max(1, qid - 1)
        next_id = min(max_id + 1, qid + 1)

        # Section options
        section_options = ""
        for s in sections:
            sel = "selected" if s["id"] == section else ""
            count = len([q2 for q2 in data["questions"] if q2["section"] == s["id"]])
            section_options += f'<option value="{s["id"]}" {sel}>{s["name"]} ({count})</option>'

        # ID grid (show 50 around current)
        grid_start = max(1, qid - 25)
        grid_end = min(max_id + 1, grid_start + 50)
        id_grid = ""
        for i in range(grid_start, grid_end + 1):
            if i in section_ids:
                cls = "id-btn exists"
            else:
                cls = "id-btn missing"
            if i == qid:
                cls += " current"
            id_grid += f'<a href="/?section={section}&id={i}" class="{cls}">{i}</a>'

        # Message
        message = ""
        if msg == "saved":
            message = '<div class="msg msg-ok">✓ Saved successfully</div>'
        elif msg == "error":
            message = '<div class="msg msg-err">✗ Error saving</div>'

        question_form = render_question_form(q, section, qid)

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
            "{message}", message
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
            if text_ru:
                q["text_ru"] = text_ru

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
        else:
            # Update existing
            q["text"] = text
            q["points"] = points
            q["correct_answers_count"] = correct_count
            if text_ru:
                q["text_ru"] = text_ru
            if image_filename:
                q["image"] = image_filename
                q["has_image"] = True

            # Update options
            opt_count = int(fields.get("options_count", "0"))
            correct_answers = []
            for i in range(opt_count):
                letter = fields.get(f"opt_{i}_letter", "")
                opt_text = fields.get(f"opt_{i}_text", "")
                opt_text_ru = fields.get(f"opt_{i}_text_ru", "")
                is_correct = f"opt_{i}_correct" in fields

                if i < len(q["options"]):
                    q["options"][i]["text"] = opt_text
                    if opt_text_ru:
                        q["options"][i]["text_ru"] = opt_text_ru

                if is_correct:
                    correct_answers.append(letter)

            if correct_answers:
                q["correct_answers"] = sorted(correct_answers)

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
    server = HTTPServer(("", PORT), VerifyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
