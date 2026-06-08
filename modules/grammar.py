import os
from modules import ui, lang
from modules.utils import load_json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
GRAMMAR_FILE = os.path.join(DATA_DIR, "grammar.json")

CATEGORIES = [
    ("tense", "Tenses", "C\u00e1c Th\u00ec", "\u23f0"),
    ("conditional", "Conditionals", "C\u00e2u \u0110i\u1ec1u Ki\u1ec7n", "\U0001f500"),
    ("comparison", "Comparisons", "So S\u00e1nh", "\u2696\ufe0f"),
    ("voice", "Passive Voice", "C\u00e2u B\u1ecb \u0110\u1ed9ng", "\U0001f504"),
    ("modals", "Modal Verbs", "\u0110\u1ed9ng T\u1eeb Khuy\u1ebft Thi\u1ebfu", "\U0001f3af"),
    ("reported", "Reported Speech", "C\u00e2u T\u01b0\u1eddng Thu\u1eadt", "\U0001f4ac"),
    ("clauses", "Clauses", "M\u1ec7nh \u0110\u1ec1", "\U0001f517"),
    ("verbals", "Gerunds & Infinitives", "Danh \u0110\u1ed9ng T\u1eeb & Nguy\u00ean M\u1eabu", "\U0001f4dd"),
    ("articles", "Articles", "M\u1ea1o T\u1eeb", "\U0001f4cc"),
    ("prepositions", "Prepositions", "Gi\u1edbi T\u1eeb", "\U0001f4cd"),
]


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


def pick_lesson(items, cat_name):
    while True:
        ui.clear()
        ui.header(cat_name)
        for item in items:
            ui.cprint(f"  {ui.S.FG.CYAN}[{item['id']}]{ui.S.RESET}  {ui.S.BOLD}{item['title']}{ui.S.RESET}  {ui.S.FG.GREEN}({item['title_vi']}){ui.S.RESET}")
        print()
        ui.cprint(f"  {ui.S.FG.RED}[0]{ui.S.RESET}  {lang.t('menu.exit')}")
        print()

        choice = ui.input_prompt(lang.t("app.choose"))

        if choice in ("0", "exit", "quit"):
            return False

        try:
            cid = int(choice)
            for item in items:
                if item["id"] == cid:
                    show_lesson(item)
                    return True
            ui.error(lang.t("app.invalid"))
            ui.wait()
        except ValueError:
            ui.error(lang.t("app.invalid"))
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

        for i, (key, name, name_vi, icon) in enumerate(CATEGORIES, 1):
            count = len([g for g in grammar if g["category"] == key])
            if count == 0:
                continue
            padded = f"{name} ({name_vi})"
            ui.cprint(f"  {ui.S.FG.CYAN}[{i}]{ui.S.RESET}  {icon}  {ui.S.BOLD}{padded}{ui.S.RESET}  {ui.S.FG.BRIGHT_BLACK}({count}){ui.S.RESET}")
        print()
        ui.cprint(f"  {ui.S.FG.RED}[0]{ui.S.RESET}  {lang.t('menu.exit')}")
        print()

        choice = ui.input_prompt(lang.t("app.choose"))

        if choice in ("0", "exit", "quit"):
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(CATEGORIES):
                key = CATEGORIES[idx][0]
                items = [g for g in grammar if g["category"] == key]
                if items:
                    cat_name = f"{CATEGORIES[idx][1]} ({CATEGORIES[idx][2]})"
                    if not pick_lesson(items, cat_name):
                        continue
            else:
                ui.error(lang.t("app.invalid"))
                ui.wait()
        except ValueError:
            ui.error(lang.t("app.invalid"))
            ui.wait()
