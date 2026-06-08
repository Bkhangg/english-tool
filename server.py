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

sys.path.insert(0, os.path.dirname(__file__))
from modules import lang
from modules.utils import (
    load_words, load_user_data, save_user_data,
    get_word_by_id, get_next_review_words, update_after_review,
    get_today_reviews,
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
    return json_response({
        "total": total,
        "learned": learned_count,
        "remaining": total - learned_count,
        "lang": load_lang_strings(),
        "reviews_today": get_today_reviews(),
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


def api_quiz():
    words = load_words()
    if len(words) < 4:
        return json_response({"error": "not enough words"}, 400)

    selected = random.sample(words, min(10, len(words)))
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

    for w in load_words():
        if w["word"].lower() == word.lower():
            result["vi_meaning"] = w.get("meaning", "")
            result["definition"] = w.get("definition", "")
            result["definition_vi"] = w.get("definition_vi", "")
            result["vi_example"] = w.get("example", "")
            result["example_vi"] = w.get("example_vi", "")
            break

    return json_response(result)


def api_lang():
    return json_response({"lang": load_lang_strings()})


def api_lang_set(body):
    l = body.get("lang")
    if l not in ("en", "vi"):
        return json_response({"error": "invalid lang"}, 400)
    lang.set_language(l)
    return json_response({"ok": True, "lang": l})


ROUTES = {
    "GET": {},
    "POST": {},
}


def route(method, path, handler):
    ROUTES[method][path] = handler


route("GET", "/api/stats", lambda q, b: api_stats())
route("GET", "/api/words", lambda q, b: api_words())
route("GET", "/api/review-words", lambda q, b: api_review_words())
route("GET", "/api/quiz", lambda q, b: api_quiz())
route("GET", "/api/lang", lambda q, b: api_lang())
route("GET", "/api/dictionary", lambda q, b: api_dictionary(urllib.parse.parse_qs(q).get("word", [""])[0]))

route("POST", "/api/review", lambda q, b: api_review(b))
route("POST", "/api/lang", lambda q, b: api_lang_set(b))


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
        threading.Timer(0.5, lambda: webbrowser.open(addr)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    run()
