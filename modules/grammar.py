import os
from modules import ui, lang
from modules.utils import load_json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
GRAMMAR_FILE = os.path.join(DATA_DIR, "grammar.json")


def load_grammar():
    return load_json(GRAMMAR_FILE).get("grammar", [])


def show_lesson(item):
    ui.clear()
    ui.header(item["title"])

    ui.cprint(f"\n  {ui.S.BOLD}{ui.S.FG.CYAN}{lang.t('grammar.formula')}:{ui.S.RESET}")
    ui.cprint(f"  {ui.S.FG.YELLOW}{item['formula']}{ui.S.RESET}")
    ui.cprint(f"  {ui.S.FG.GREEN}{item['formula_vi']}{ui.S.RESET}")

    ui.cprint(f"\n  {ui.S.BOLD}{ui.S.FG.CYAN}{lang.t('grammar.usage')}:{ui.S.RESET}")
    ui.cprint(f"  {item['usage']}")
    ui.cprint(f"  {ui.S.FG.GREEN}{item['usage_vi']}{ui.S.RESET}")

    if item.get("keywords"):
        ui.cprint(f"\n  {ui.S.BOLD}{ui.S.FG.CYAN}{lang.t('grammar.keywords')}:{ui.S.RESET}")
        ui.cprint(f"  {ui.S.FG.BRIGHT_BLACK}{', '.join(item['keywords'])}{ui.S.RESET}")

    ui.cprint(f"\n  {ui.S.BOLD}{ui.S.FG.CYAN}{lang.t('grammar.examples')}:{ui.S.RESET}")
    for i, ex in enumerate(item["examples"], 1):
        ui.cprint(f"  {ui.S.FG.BRIGHT_BLACK}{i}.{ui.S.RESET} {ex['en']}")
        ui.cprint(f"     {ui.S.FG.GREEN}{ex['vi']}{ui.S.RESET}")
        if i < len(item["examples"]):
            print()

    print()
    ui.wait()


def run():
    grammar = load_grammar()
    if not grammar:
        ui.error(lang.t("grammar.empty"))
        ui.wait()
        return

    while True:
        ui.clear()
        ui.header(lang.t("grammar.header"))
        ui.cprint(f"  {ui.S.FG.BRIGHT_BLACK}{lang.t('grammar.category.tense')}:{ui.S.RESET}")
        tenses = [g for g in grammar if g["category"] == "tense"]
        for item in tenses:
            ui.cprint(f"    {ui.S.FG.CYAN}[{item['id']}]{ui.S.RESET}  {ui.S.BOLD}{item['title']}{ui.S.RESET}  {ui.S.FG.GREEN}({item['title_vi']}){ui.S.RESET}")
        print()
        ui.cprint(f"  {ui.S.FG.BRIGHT_BLACK}{lang.t('grammar.category.conditional')}:{ui.S.RESET}")
        conds = [g for g in grammar if g["category"] == "conditional"]
        for item in conds:
            ui.cprint(f"    {ui.S.FG.CYAN}[{item['id']}]{ui.S.RESET}  {ui.S.BOLD}{item['title']}{ui.S.RESET}  {ui.S.FG.GREEN}({item['title_vi']}){ui.S.RESET}")
        print()
        ui.cprint(f"  {ui.S.FG.RED}[0]{ui.S.RESET}  {lang.t('menu.exit')}")
        print()

        choice = ui.input_prompt(lang.t("app.choose"))

        if choice in ("0", "exit", "quit"):
            return

        try:
            cid = int(choice)
            for item in grammar:
                if item["id"] == cid:
                    show_lesson(item)
                    break
            else:
                ui.error(lang.t("app.invalid"))
                ui.wait()
        except ValueError:
            ui.error(lang.t("app.invalid"))
            ui.wait()
