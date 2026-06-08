import http.server
import json
import os
import urllib.parse
import urllib.request
import urllib.error
import sys
import random
import webbrowser
import threading
import subprocess

sys.path.insert(0, os.path.dirname(__file__))
from modules import lang
from modules.utils import (
    load_words, load_user_data, save_user_data,
    get_word_by_id, get_next_review_words, update_after_review,
    get_today_reviews, get_streak,
)

DICT_API = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
GT_API = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=vi&dt=t&q={text}"
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
PORT = int(os.environ.get("PORT", 8000))


def translate_batch(texts):
    if not texts:
        return {}
    batch = "\n".join(texts)
    if len(batch) > 1500:
        return {}
    url = GT_API.format(text=urllib.parse.quote(batch))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = "".join(x[0] for x in data[0]).strip()
            if result:
                parts = result.split("\n")
                return {texts[i]: parts[i] for i in range(min(len(texts), len(parts)))}
    except Exception:
        pass
    return {}


def load_lang_strings():
    user_data = load_user_data()
    l = user_data.get("settings", {}).get("language", "vi")
    return l


def json_response(data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return (status, {"Content-Type": "application/json; charset=utf-8"}, body)


def api_stats():
    words = load_words()
    user_data = load_user_data()
    learned = user_data.get("learned", {})
    total = len(words)
    learned_count = len(learned)
    streak = get_streak()
    return json_response({
        "total": total,
        "learned": learned_count,
        "remaining": total - learned_count,
        "lang": load_lang_strings(),
        "reviews_today": get_today_reviews(),
        "streak": streak.get("current", 0),
        "streak_longest": streak.get("longest", 0),
    })


def api_words():
    words = load_words()
    user_data = load_user_data()
    learned = user_data.get("learned", {})
    result = []
    for w in words:
        wid = str(w["id"])
        info = learned.get(wid, {})
        result.append({
            "id": w["id"],
            "word": w["word"],
            "ipa": w.get("ipa", ""),
            "meaning": w.get("meaning", ""),
            "definition": w.get("definition", ""),
            "definition_vi": w.get("definition_vi", ""),
            "example": w.get("example", ""),
            "example_vi": w.get("example_vi", ""),
            "learned": wid in learned,
            "level": info.get("level", 0),
        })
    return json_response({"words": result, "total": len(result)})


def api_add_word(body):
    word = body.get("word", "").strip()
    meaning = body.get("meaning", "").strip()
    if not word or not meaning:
        return json_response({"error": "missing word or meaning"}, 400)
    words = load_words()
    word_lower = word.lower()
    if any(w["word"].lower() == word_lower for w in words):
        return json_response({"error": "word already exists"}, 409)
    new_id = max(w["id"] for w in words) + 1 if words else 1
    entry = {
        "id": new_id,
        "word": word,
        "ipa": body.get("ipa", ""),
        "meaning": meaning,
        "definition": body.get("definition", ""),
        "definition_vi": body.get("definition_vi", ""),
        "example": body.get("example", ""),
        "example_vi": body.get("example_vi", ""),
    }
    from modules.utils import WORDS_FILE
    import json, os
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["words"].append(entry)
    with open(WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return json_response({"ok": True, "id": new_id})


def api_review_words():
    words = get_next_review_words(limit=10)
    data = []
    for w in words:
        data.append({
            "id": w["id"],
            "word": w["word"],
            "ipa": w.get("ipa", ""),
            "meaning": w.get("meaning", ""),
            "definition": w.get("definition", ""),
            "definition_vi": w.get("definition_vi", ""),
            "example": w.get("example", ""),
            "example_vi": w.get("example_vi", ""),
        })
    return json_response({"words": data, "total": len(data)})


def api_review(body):
    word_id = body.get("word_id")
    known = body.get("known", True)
    if word_id is None:
        return json_response({"error": "missing word_id"}, 400)
    update_after_review(word_id, known)
    return json_response({"ok": True})


def api_quiz(qs=""):
    words = load_words()
    if len(words) < 4:
        return json_response({"error": "not enough words"}, 400)

    params = urllib.parse.parse_qs(qs)
    ud = load_user_data()
    default_count = ud.get("settings", {}).get("quiz_count", 10)
    count = int(params.get("count", [default_count])[0]) if params.get("count") else default_count
    count = max(4, min(count, len(words)))
    selected = random.sample(words, count)
    questions = []
    for w in selected:
        wrong = random.sample([x for x in words if x["id"] != w["id"]], 3)
        options = [w["meaning"]] + [x["meaning"] for x in wrong]
        random.shuffle(options)
        questions.append({
            "word": w["word"],
            "ipa": w.get("ipa", ""),
            "correct": w["meaning"],
            "options": options,
        })
    return json_response({"questions": questions, "total": len(questions)})


def api_dictionary(word):
    url = DICT_API.format(word=urllib.parse.quote(word))
    req = urllib.request.Request(url, headers={"User-Agent": "EnglishTool/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return json_response({"not_found": True})
        return json_response({"error": "lookup failed"}, 502)
    except urllib.error.URLError:
        return json_response({"error": "network error"}, 502)

    result = {"word": data[0].get("word", word), "meanings": []}

    texts = []
    for m in data[0].get("meanings", []):
        for d in m.get("definitions", [])[:3]:
            if d.get("definition"):
                texts.append(d["definition"])
            if d.get("example"):
                texts.append(d["example"])
    trans = translate_batch(texts)

    for m in data[0].get("meanings", []):
        pos = m.get("partOfSpeech", "")
        defs = []
        for d in m.get("definitions", [])[:3]:
            entry = {"definition": d.get("definition", "")}
            if d.get("definition") and d["definition"] in trans:
                entry["definition_vi"] = trans[d["definition"]]
            if d.get("example"):
                entry["example"] = d["example"]
                if d["example"] in trans:
                    entry["example_vi"] = trans[d["example"]]
            if d.get("synonyms"):
                entry["synonyms"] = d["synonyms"][:3]
            defs.append(entry)
        result["meanings"].append({"partOfSpeech": pos, "definitions": defs})

    phonetics = data[0].get("phonetics", [])
    for p in phonetics:
        if p.get("text"):
            result["ipa"] = p["text"]
            break
    for p in phonetics:
        if p.get("audio"):
            result["audio"] = p["audio"]
            break

    result["in_wordlist"] = False
    for w in load_words():
        if w["word"].lower() == word.lower():
            result["in_wordlist"] = True
            result["vi_meaning"] = w.get("meaning", "")
            result["definition"] = w.get("definition", "")
            result["definition_vi"] = w.get("definition_vi", "")
            result["vi_example"] = w.get("example", "")
            result["example_vi"] = w.get("example_vi", "")
            result["word_id"] = w["id"]
            break

    return json_response(result)


def api_grammar():
    from modules.utils import load_json
    import os
    path = os.path.join(os.path.dirname(__file__), "data", "grammar.json")
    data = load_json(path)
    return json_response(data.get("grammar", []))


def api_grammar_quiz():
    import os
    from modules.utils import load_json
    path = os.path.join(os.path.dirname(__file__), "data", "grammar.json")
    data = load_json(path).get("grammar", [])
    if len(data) < 2:
        return json_response({"error": "not enough grammar items"}, 400)

    n = min(10, len(data))
    selected = random.sample(data, n)
    questions = []

    for item in selected:
        others = [x for x in data if x["id"] != item["id"]]
        qtype = random.choice(["formula", "usage", "identify"])

        if qtype == "formula":
            question = f"What is the formula of \"{item['title']}\"? / Công thức của \"{item['title_vi']}\" là gì?"
            correct = item["formula"]
            wrong = random.sample([x["formula"] for x in others], min(3, len(others)))
            options = [correct] + wrong
        elif qtype == "usage":
            question = f"What is \"{item['title']}\" used for? / \"{item['title_vi']}\" dùng để làm gì?"
            correct = item["usage"]
            wrong = random.sample([x["usage"] for x in others], min(3, len(others)))
            options = [correct] + wrong
        else:
            ex = random.choice(item["examples"])
            question = f"Which grammar point is this? / Đây là ngữ pháp gì?\n\"{ex['en']}\""
            correct = item["title"]
            wrong = random.sample([x["title"] for x in others], min(3, len(others)))
            options = [correct] + wrong

        random.shuffle(options)
        questions.append({
            "question": question,
            "correct": correct,
            "options": options,
            "grammar_title": item["title"],
            "grammar_title_vi": item["title_vi"],
        })

    return json_response({"questions": questions, "total": len(questions)})


def api_lang():
    return json_response({"lang": load_lang_strings()})


def api_lang_set(body):
    l = body.get("lang")
    if l not in ("en", "vi"):
        return json_response({"error": "invalid lang"}, 400)
    lang.set_language(l)
    return json_response({"ok": True, "lang": l})


def api_export():
    user_data = load_user_data()
    words = load_words()
    return json_response({
        "user_data": user_data,
        "custom_words": [],
    })


def api_import(body):
    ud = body.get("user_data")
    if ud:
        save_user_data(ud)
    return json_response({"ok": True})


def api_settings_get():
    ud = load_user_data()
    s = ud.get("settings", {})
    return json_response({
        "quiz_count": s.get("quiz_count", 10),
        "tts_speed": s.get("tts_speed", 0.85),
        "show_ipa": s.get("show_ipa", True),
        "font_family": s.get("font_family", "system"),
        "theme": s.get("theme", "dark"),
    })


def api_settings_set(body):
    ud = load_user_data()
    s = ud.setdefault("settings", {})
    for k in ("quiz_count", "tts_speed", "show_ipa", "font_family", "theme"):
        if k in body:
            s[k] = body[k]
    save_user_data(ud)
    return json_response({"ok": True})


ROUTES = {
    "GET": {},
    "POST": {},
}


def route(method, path, handler):
    ROUTES[method][path] = handler


route("GET", "/api/stats", lambda q, b: api_stats())
route("GET", "/api/words", lambda q, b: api_words())
route("GET", "/api/review-words", lambda q, b: api_review_words())
route("GET", "/api/quiz", lambda q, b: api_quiz(q))
route("GET", "/api/grammar", lambda q, b: api_grammar())
route("GET", "/api/grammar-quiz", lambda q, b: api_grammar_quiz())
route("GET", "/api/lang", lambda q, b: api_lang())
route("GET", "/api/dictionary", lambda q, b: api_dictionary(urllib.parse.parse_qs(q).get("word", [""])[0]))

route("POST", "/api/review", lambda q, b: api_review(b))
route("POST", "/api/lang", lambda q, b: api_lang_set(b))
route("POST", "/api/words", lambda q, b: api_add_word(b))
route("GET", "/api/export", lambda q, b: api_export())
route("GET", "/api/settings", lambda q, b: api_settings_get())
route("POST", "/api/settings", lambda q, b: api_settings_set(b))
route("POST", "/api/import", lambda q, b: api_import(b))


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, status, headers, body):
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ROUTES["GET"]:
            status, headers, body = ROUTES["GET"][path](parsed.query, None)
            self._send(status, headers, body)
            return

        if path.startswith("/api/"):
            self._send(404, {"Content-Type": "application/json"}, b'{"error":"not found"}')
            return

        if path == "/":
            path = "/index.html"

        file_path = os.path.join(WEB_DIR, path.lstrip("/"))
        file_path = os.path.normpath(file_path)

        if not file_path.startswith(os.path.normpath(WEB_DIR)):
            self._send(403, {}, b"Forbidden")
            return

        if not os.path.isfile(file_path):
            file_path = os.path.join(WEB_DIR, "index.html")

        ext = os.path.splitext(file_path)[1]
        mime = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".svg": "image/svg+xml",
        }.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                body = f.read()
            self._send(200, {"Content-Type": mime}, body)
        except FileNotFoundError:
            self._send(404, {}, b"Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path not in ROUTES["POST"]:
            self._send(404, {"Content-Type": "application/json"}, b'{"error":"not found"}')
            return

        content_len = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_len) if content_len else b"{}"
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {}

        if path == "/api/review":
            result = api_review(body)
        elif path == "/api/lang":
            result = api_lang_set(body)
        else:
            self._send(404, {"Content-Type": "application/json"}, b'{"error":"not found"}')
            return

        self._send(*result)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run():
    addr = f"http://localhost:{PORT}"

    try:
        term = os.environ.get("TERMUX_VERSION")
        is_termux = term is not None
    except Exception:
        is_termux = False

    prompt = (
        f"Open {addr} in browser? [Y/n]: "
        if is_termux
        else f"Open {addr} in browser? (y/N): "
    )
    try:
        choice = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        choice = ""

    auto_open = is_termux and choice != "n"
    if not is_termux:
        auto_open = choice == "y"

    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n  Server running at {addr}")
    print(f"  Press Ctrl+C to stop\n")

    if auto_open:
        if is_termux:
            threading.Timer(0.5, lambda: subprocess.run(["termux-open-url", addr], capture_output=True)).start()
        else:
            threading.Timer(0.5, lambda: webbrowser.open(addr)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    run()
