#!/usr/bin/env python3
import sys
from modules import ui, lang
from modules.utils import show_stats


def settings_menu():
    while True:
        ui.clear()
        ui.header(lang.t("app.settings"))

        current = lang.get_language()
        lang_name = lang.t("app.lang_en") if current == "en" else lang.t("app.lang_vi")

        ui.cprint(f"  {ui.S.FG.WHITE}{lang.t('app.lang_prompt')}:{ui.S.RESET}  {ui.S.FG.YELLOW}{lang_name}{ui.S.RESET}")
        print()
        ui.cprint(f"  {ui.S.FG.CYAN}[1]{ui.S.RESET}  {lang.t('app.lang_en')}")
        ui.cprint(f"  {ui.S.FG.CYAN}[2]{ui.S.RESET}  {lang.t('app.lang_vi')}")
        print()
        ui.cprint(f"  {ui.S.FG.RED}[0]{ui.S.RESET}  {lang.t('menu.exit')}")
        print()

        choice = ui.input_prompt(lang.t("app.choose"))

        if choice == "1":
            if lang.set_language("en"):
                ui.success("Language changed to English")
            ui.wait()
        elif choice == "2":
            if lang.set_language("vi"):
                ui.success("\u0110\u00e3 chuy\u1ec3n sang ti\u1ebfng Vi\u1ec7t")
            ui.wait()
        elif choice in ("0", "exit", "quit"):
            return
        else:
            ui.error(lang.t("app.invalid"))
            ui.wait()


def add_word_cli():
    from modules.utils import load_words, save_json, WORDS_FILE
    import json
    ui.clear()
    ui.header(lang.t("menu.add_word"))
    word = ui.input_prompt(f"{lang.t('words_add_word')}: ")
    if not word:
        return
    meaning = ui.input_prompt(f"{lang.t('words_add_meaning')}: ")
    if not meaning:
        return
    ipa = ui.input_prompt(f"{lang.t('words_add_ipa')} (Enter to skip): ")
    example = ui.input_prompt(f"{lang.t('words_add_example')} (Enter to skip): ")

    words = load_words()
    if any(w["word"].lower() == word.lower() for w in words):
        ui.error(lang.t("words_add_exists"))
        ui.wait()
        return

    new_id = max(w["id"] for w in words) + 1 if words else 1
    entry = {
        "id": new_id,
        "word": word,
        "ipa": ipa,
        "meaning": meaning,
        "definition": "",
        "definition_vi": "",
        "example": example,
        "example_vi": "",
    }
    data = {"words": words + [entry]}
    save_json(WORDS_FILE, data)
    ui.success(f"{lang.t('words_add_success')}: {word}")
    ui.wait()


def auto_fetch_cli():
    from modules.utils import fetch_random_word, load_words, save_json, WORDS_FILE
    import json
    ui.clear()
    ui.header(lang.t("menu.auto_fetch"))
    ui.cprint(f"  {ui.S.FG.YELLOW}{lang.t('auto_fetch.fetching')}{ui.S.RESET}\n")

    result = fetch_random_word()
    if not result:
        ui.error(lang.t("auto_fetch.error"))
        ui.wait()
        return

    words = load_words()
    if any(w["word"].lower() == result["word"].lower() for w in words):
        ui.error(f"\"{result['word']}\" {lang.t('auto_fetch.exists')}")
        ui.wait()
        return

    ui.cprint(f"  {ui.S.BOLD}{ui.S.FG.CYAN}{result['word']}{ui.S.RESET}")
    if result["ipa"]:
        ui.cprint(f"  {ui.S.FG.BRIGHT_BLACK}{result['ipa']}{ui.S.RESET}")
    ui.cprint(f"  {ui.S.FG.GREEN}{result['meaning']}{ui.S.RESET}")
    if result["definition"]:
        ui.cprint(f"  {ui.S.FG.BRIGHT_BLACK}{result['definition']}{ui.S.RESET}")
    if result["definition_vi"]:
        ui.cprint(f"  {ui.S.FG.GREEN}{result['definition_vi']}{ui.S.RESET}")
    if result["example"]:
        ui.cprint(f"  \"{ui.S.FG.BRIGHT_BLACK}{result['example']}{ui.S.RESET}\"")
    print()

    choice = ui.input_prompt(lang.t("auto_fetch.prompt")).strip().lower()
    if choice in ("y", "yes", ""):
        new_id = max(w["id"] for w in words) + 1 if words else 1
        result["id"] = new_id
        data = {"words": words + [result]}
        save_json(WORDS_FILE, data)
        ui.success(f"{lang.t('auto_fetch.saved')} \"{result['word']}\"")
    else:
        ui.cprint(f"  {ui.S.FG.YELLOW}{lang.t('auto_fetch.skip')}{ui.S.RESET}")
    ui.wait()


def show_menu():
    while True:
        ui.clear()
        ui.banner()

        items = [
            ("1", lang.t("menu.flashcards"), lang.t("menu.desc.flashcards")),
            ("2", lang.t("menu.dictionary"), lang.t("menu.desc.dictionary")),
            ("3", lang.t("menu.quiz"), lang.t("menu.desc.quiz")),
            ("4", lang.t("menu.grammar"), lang.t("menu.desc.grammar")),
            ("5", lang.t("menu.progress"), lang.t("menu.desc.progress")),
            ("6", lang.t("menu.settings"), lang.t("menu.desc.settings")),
            ("7", lang.t("menu.add_word"), lang.t("menu.desc.add_word")),
            ("8", lang.t("menu.auto_fetch"), lang.t("menu.desc.auto_fetch")),
        ]

        max_name = max(ui.visible_len(n) for _, n, _ in items)
        num_w = max(ui.visible_len(str(i)) for i, _, _ in items) + 1

        for num, name, desc in items:
            padded_name = name + " " * (max_name - ui.visible_len(name) + 2)
            ui.cprint(f"  {ui.S.BOLD}{ui.S.FG.CYAN}[{num}]{ui.S.RESET}  {ui.S.BOLD}{padded_name}{ui.S.RESET}{ui.S.FG.BRIGHT_BLACK}{desc}{ui.S.RESET}")

        exit_name = lang.t("menu.exit")
        exit_padded = exit_name + " " * (max_name - ui.visible_len(exit_name) + 2)
        ui.cprint(f"  {ui.S.BOLD}{ui.S.FG.RED}[0]{ui.S.RESET}  {ui.S.BOLD}{exit_padded}{ui.S.RESET}{ui.S.FG.BRIGHT_BLACK}{lang.t('menu.desc.exit')}{ui.S.RESET}")
        print()

        choice = ui.input_prompt(lang.t("app.choose"))

        if choice == "1":
            from modules.flashcard import run as flashcard_run
            flashcard_run()
        elif choice == "2":
            from modules.dictionary import run as dict_run
            dict_run()
        elif choice == "3":
            from modules.quiz import run as quiz_run
            quiz_run()
        elif choice == "4":
            from modules.grammar import run as grammar_run
            grammar_run()
        elif choice == "5":
            ui.clear()
            show_stats()
            ui.wait()
        elif choice == "6":
            settings_menu()
        elif choice == "7":
            add_word_cli()
        elif choice == "8":
            auto_fetch_cli()
        elif choice in ("0", "exit", "quit"):
            ui.clear()
            ui.cprint(f"\n  {ui.S.BOLD}{ui.S.FG.CYAN}{lang.t('app.exit_msg')} \u2606{ui.S.RESET}\n")
            sys.exit(0)
        else:
            ui.error(lang.t("app.invalid"))
            ui.wait()


if __name__ == "__main__":
    ui.init()
    show_menu()
