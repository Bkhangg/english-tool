import json
import os
from datetime import datetime, timedelta
from modules import ui, lang

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
WORDS_FILE = os.path.join(DATA_DIR, "words.json")
USER_FILE = os.path.join(DATA_DIR, "user_data.json")


def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_words():
    return load_json(WORDS_FILE).get("words", [])


def load_user_data():
    return load_json(USER_FILE)


def save_user_data(data):
    save_json(USER_FILE, data)


def get_word_by_id(word_id):
    words = load_words()
    for w in words:
        if w["id"] == word_id:
            return w
    return None


def get_words_by_levels(levels, limit=10):
    user_data = load_user_data()
    learned = user_data.get("learned", {})
    words = load_words()
    filtered = []
    for w in words:
        wid = str(w["id"])
        info = learned.get(wid, {})
        lvl = info.get("level", 0) if wid in learned else 0
        if lvl in levels:
            filtered.append(w)
    return filtered[:limit]


def get_next_review_words(limit=10):
    user_data = load_user_data()
    now = datetime.now().isoformat()
    learned = user_data.get("learned", {})

    review_words = []
    for word_id, info in learned.items():
        next_review = info.get("next_review")
        if next_review and next_review <= now:
            word = get_word_by_id(int(word_id))
            if word:
                review_words.append(word)

    words = load_words()
    new_words = [w for w in words if str(w["id"]) not in learned]

    all_words = review_words + new_words
    return all_words[:limit]


def update_after_review(word_id, correct):
    user_data = load_user_data()
    learned = user_data.setdefault("learned", {})
    wid = str(word_id)
    info = learned.get(wid, {"level": 0, "correct_streak": 0, "next_review": None})

    if correct:
        info["correct_streak"] = info.get("correct_streak", 0) + 1
        level = min(info["correct_streak"] // 3, 5)
        info["level"] = level
        intervals = [0, 1, 3, 7, 14, 30]
        days = intervals[min(level, len(intervals) - 1)]
        info["next_review"] = (datetime.now() + timedelta(days=days)).isoformat()
    else:
        info["correct_streak"] = 0
        info["level"] = 0
        info["next_review"] = datetime.now().isoformat()

    learned[wid] = info

    today = datetime.now().strftime("%Y-%m-%d")
    stats = user_data.setdefault("stats", {})
    if stats.get("last_date") != today:
        stats["reviews_today"] = 1
        stats["last_date"] = today
    else:
        stats["reviews_today"] = stats.get("reviews_today", 0) + 1

    save_user_data(user_data)
    update_streak()


def get_today_reviews():
    user_data = load_user_data()
    stats = user_data.get("stats", {})
    today = datetime.now().strftime("%Y-%m-%d")
    if stats.get("last_date") != today:
        return 0
    return stats.get("reviews_today", 0)


def update_streak():
    user_data = load_user_data()
    streak = user_data.setdefault("streak", {"current": 0, "longest": 0, "last_date": ""})
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if streak["last_date"] == today:
        pass
    elif streak["last_date"] == yesterday:
        streak["current"] += 1
    elif streak["last_date"]:
        streak["current"] = 1
    else:
        streak["current"] = 1

    streak["last_date"] = today
    if streak["current"] > streak["longest"]:
        streak["longest"] = streak["current"]

    save_user_data(user_data)


def get_streak():
    user_data = load_user_data()
    return user_data.get("streak", {"current": 0, "longest": 0})


def _translate_texts(texts):
    import urllib.request
    import urllib.parse
    import json
    if not texts:
        return {}
    batch = "\n".join(texts)
    if len(batch) > 1500:
        return {}
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=vi&dt=t&q=" + urllib.parse.quote(batch)
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


def fetch_random_word():
    import urllib.request
    import urllib.parse
    import json
    import random

    fallback_words = [
        "abandon", "absorb", "accept", "accuse", "achieve", "acquire", "adapt",
        "adjust", "admire", "admit", "adopt", "advise", "afford", "announce",
        "apologize", "appear", "applaud", "appreciate", "approach", "arrange",
        "arrive", "assume", "assure", "astonish", "attach", "attempt", "attend",
        "attract", "balance", "beg", "behave", "belong", "blame", "borrow",
        "bother", "breathe", "bury", "calculate", "capture", "celebrate",
        "challenge", "collapse", "command", "compare", "compete", "complain",
        "confess", "confuse", "connect", "conquer", "consider", "consist",
        "consult", "contain", "continue", "contribute", "convince", "correct",
        "create", "criticize", "decide", "declare", "decline", "decorate",
        "defend", "define", "deliver", "demand", "deny", "depend", "describe",
        "deserve", "desire", "destroy", "determine", "develop", "devote",
        "discover", "discuss", "display", "distinguish", "disturb", "divide",
        "doubt", "earn", "educate", "employ", "enable", "encounter", "encourage",
        "engage", "enhance", "enjoy", "ensure", "entertain", "establish",
        "evaluate", "examine", "exceed", "exchange", "exclude", "excuse",
        "exercise", "exist", "expand", "expect", "explain", "explore",
        "express", "extend", "extract", "fascinate", "forbid", "forecast",
        "forgive", "form", "generate", "guarantee", "hesitate", "identify",
        "ignore", "illustrate", "imagine", "imitate", "imply", "impose",
        "impress", "improve", "include", "indicate", "inform", "inhabit",
        "insist", "inspire", "install", "integrate", "intend", "interfere",
        "interpret", "interrupt", "introduce", "invent", "invest", "investigate",
        "involve", "isolate", "maintain", "manage", "manufacture", "measure",
        "mention", "motivate", "negotiate", "observe", "obtain", "occupy",
        "operate", "oppose", "organize", "overcome", "perform", "persist",
        "persuade", "possess", "predict", "prepare", "preserve", "prevent",
        "produce", "promise", "promote", "propose", "protest", "purchase",
        "pursue", "qualify", "question", "realize", "recall", "recognize",
        "recommend", "recover", "reduce", "refer", "reflect", "refuse",
        "regret", "reject", "relate", "release", "rely", "remain", "remind",
        "remove", "replace", "represent", "request", "require", "rescue",
        "resign", "resist", "resolve", "respect", "respond", "restore",
        "restrict", "reveal", "revolt", "sacrifice", "satisfy", "scatter",
        "seize", "select", "separate", "settle", "submit", "subtract",
        "succeed", "suggest", "supply", "support", "suppose", "surround",
        "survive", "suspect", "suspend", "tolerate", "transform", "translate",
        "tremble", "trust", "undertake", "unite", "update", "urge", "utilize",
        "vanish", "wander", "warn", "whisper", "worship", "wrap", "yield",
    ]

    def _get_random_word():
        try:
            req = urllib.request.Request(
                "https://random-word-api.herokuapp.com/word",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                words = json.loads(resp.read().decode("utf-8"))
                if words and words[0]:
                    return words[0]
        except Exception:
            pass
        return random.choice(fallback_words)

    max_attempts = 5
    for _ in range(max_attempts):
        word = _get_random_word()
        dict_url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + urllib.parse.quote(word)
        try:
            req = urllib.request.Request(dict_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            continue

        result = {
            "word": word, "ipa": "", "meaning": "",
            "definition": "", "definition_vi": "",
            "example": "", "example_vi": "",
        }

        for p in data[0].get("phonetics", []):
            if p.get("text"):
                result["ipa"] = p["text"]
                break

        for m in data[0].get("meanings", []):
            for d in m.get("definitions", []):
                if d.get("definition"):
                    result["definition"] = d["definition"]
                    if d.get("example"):
                        result["example"] = d["example"]
                    break
            if result["definition"]:
                break

        texts = []
        if result["definition"]:
            texts.append(result["definition"])
        if result["example"]:
            texts.append(result["example"])

        if texts:
            trans = _translate_texts(texts)
            if result["definition"] in trans:
                result["definition_vi"] = trans[result["definition"]]
            if result["example"] in trans:
                result["example_vi"] = trans[result["example"]]

        if result["definition_vi"]:
            result["meaning"] = result["definition_vi"].split(".")[0].split(";")[0][:60].strip()
        else:
            result["meaning"] = word

        return result

    return None


def fetch_random_words(count=1):
    words = load_words()
    existing = {w["word"].lower() for w in words}
    results = []
    attempts = 0
    while len(results) < count and attempts < count * 5:
        r = fetch_random_word()
        attempts += 1
        if r and r["word"].lower() not in existing:
            existing.add(r["word"].lower())
            results.append(r)
    return results


def show_stats():
    words = load_words()
    user_data = load_user_data()
    learned = user_data.get("learned", {})
    total = len(words)
    learned_count = len(learned)
    remaining = total - learned_count
    streak = get_streak()

    words_icon = "W:" if not ui.USE_UNICODE else "\U0001f4da"
    learned_icon = "L:" if not ui.USE_UNICODE else "\u2705"
    remaining_icon = "R:" if not ui.USE_UNICODE else "\U0001f4dd"

    today_reviews = get_today_reviews()
    streak_str = f"🔥 {streak.get('current', 0)} days" if ui.USE_UNICODE else f"Streak: {streak.get('current', 0)} days"

    lines = [
        f"{ui.S.BOLD}{ui.S.FG.WHITE}{words_icon}  {lang.t('stats.total')}{ui.S.RESET}  {total}",
        f"{ui.S.BOLD}{ui.S.FG.GREEN}{learned_icon}  {lang.t('stats.learned')}{ui.S.RESET}  {learned_count}",
        f"{ui.S.BOLD}{ui.S.FG.YELLOW}{remaining_icon}  {lang.t('stats.remaining')}{ui.S.RESET}  {remaining}",
        f"{ui.S.BOLD}{ui.S.FG.CYAN}{lang.t('prog_today')}{ui.S.RESET}  {today_reviews}",
        f"{ui.S.BOLD}{ui.S.FG.YELLOW}{streak_str}{ui.S.RESET}",
        "",
        ui.progress_bar(learned_count, total, 30),
    ]
    ui.box(lang.t("stats.title"), lines)
