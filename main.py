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


def show_menu():
    while True:
        ui.clear()
        ui.banner()

        items = [
            ("1", lang.t("menu.flashcards"), lang.t("menu.desc.flashcards")),
            ("2", lang.t("menu.dictionary"), lang.t("menu.desc.dictionary")),
            ("3", lang.t("menu.quiz"), lang.t("menu.desc.quiz")),
            ("4", lang.t("menu.progress"), lang.t("menu.desc.progress")),
            ("5", lang.t("menu.settings"), lang.t("menu.desc.settings")),
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
            ui.clear()
            show_stats()
            ui.wait()
        elif choice == "5":
            settings_menu()
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
