import urllib.request
import urllib.error
import urllib.parse
import json
from modules import ui, lang
from modules.utils import load_words

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"


def fetch_word_data(word):
    url = API_URL.format(word=urllib.parse.quote(word))
    ui.spin(f"{lang.t('dictionary.lookup')} '{word}'")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except urllib.error.URLError:
        ui.error(lang.t("dictionary.network"))
        return None


def find_local_word(word):
    words = load_words()
    for w in words:
        if w["word"].lower() == word.lower():
            return w
    return None


def display_word(data, local_word):
    is_vi = lang.get_language() == "vi"

    if not data and not local_word:
        ui.error(lang.t("dictionary.notfound"))
        return

    word = (data[0]["word"] if data else local_word["word"]).upper()

    lines = [f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('dictionary.word')}{ui.S.RESET}  {ui.S.FG.YELLOW}{word}{ui.S.RESET}"]

    if data:
        entry = data[0]
        phonetics = entry.get("phonetics", [])
        for p in phonetics:
            if p.get("text"):
                lines.append(f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('dictionary.ipa')}{ui.S.RESET}   {ui.S.FG.CYAN}{p['text']}{ui.S.RESET}")
                break
        audio = next((p.get("audio") for p in phonetics if p.get("audio")), None)
        if audio:
            lines.append(f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('dictionary.audio')}{ui.S.RESET} {ui.S.FG.BRIGHT_BLACK}{audio}{ui.S.RESET}")
    elif local_word and local_word.get("ipa"):
        lines.append(f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('dictionary.ipa')}{ui.S.RESET}   {ui.S.FG.CYAN}{local_word['ipa']}{ui.S.RESET}")

    ui.box(word, lines)

    if is_vi and local_word:
        vi_lines = [
            f"{ui.S.FG.GREEN}{ui.S.BOLD}{local_word['meaning']}{ui.S.RESET}",
        ]
        if local_word.get("example"):
            vi_lines.append(f"  {ui.S.FG.BRIGHT_BLACK}\u25b8 {local_word['example']}{ui.S.RESET}")
        ui.box(lang.t("dictionary.vi_meaning"), vi_lines)

    if data:
        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "")
            pos_lines = []
            for i, definition in enumerate(meaning.get("definitions", [])[:3], 1):
                pos_lines.append(f"{ui.S.BOLD}{ui.S.FG.CYAN}{i}.{ui.S.RESET} {definition.get('definition', '')}")
                example = definition.get("example")
                if example:
                    pos_lines.append(f"   {ui.S.FG.BRIGHT_BLACK}\u25b8 {example}{ui.S.RESET}")
                synonyms = definition.get("synonyms", [])
                if synonyms:
                    pos_lines.append(f"   {ui.S.FG.GREEN}\u21bb {', '.join(synonyms[:3])}{ui.S.RESET}")

            ui.box(pos.upper(), pos_lines)

    ui.wait()


def run():
    ui.clear()
    ui.header(lang.t("dictionary.header"), lang.t("dictionary.subtitle"))

    word = ui.input_prompt(lang.t("dictionary.prompt"))
    if not word:
        return

    local_word = find_local_word(word)
    data = fetch_word_data(word)
    display_word(data, local_word)
