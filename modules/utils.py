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
    save_user_data(user_data)


def show_stats():
    words = load_words()
    user_data = load_user_data()
    learned = user_data.get("learned", {})
    total = len(words)
    learned_count = len(learned)
    remaining = total - learned_count

    words_icon = "W:" if not ui.USE_UNICODE else "\U0001f4da"
    learned_icon = "L:" if not ui.USE_UNICODE else "\u2705"
    remaining_icon = "R:" if not ui.USE_UNICODE else "\U0001f4dd"

    lines = [
        f"{ui.S.BOLD}{ui.S.FG.WHITE}{words_icon}  {lang.t('stats.total')}{ui.S.RESET}  {total}",
        f"{ui.S.BOLD}{ui.S.FG.GREEN}{learned_icon}  {lang.t('stats.learned')}{ui.S.RESET}  {learned_count}",
        f"{ui.S.BOLD}{ui.S.FG.YELLOW}{remaining_icon}  {lang.t('stats.remaining')}{ui.S.RESET}  {remaining}",
        "",
        ui.progress_bar(learned_count, total, 30),
    ]
    ui.box(lang.t("stats.title"), lines)
