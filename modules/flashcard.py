from modules import ui, lang
from modules.utils import load_words, update_after_review, get_next_review_words, show_stats


def run():
    words = load_words()
    if not words:
        ui.error(lang.t("flashcard.empty"))
        ui.wait()
        return

    review_words = get_next_review_words(limit=10)
    if not review_words:
        ui.info(lang.t("flashcard.none"))
        ui.wait()
        return

    total = len(review_words)
    correct_count = 0

    for i, word in enumerate(review_words, 1):
        ui.clear()
        ui.header(lang.t("flashcard.header", i=i, total=total), lang.t("flashcard.reveal"))

        lines = [
            f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('flashcard.word')}{ui.S.RESET}      {ui.S.FG.YELLOW}{word['word'].upper()}{ui.S.RESET}",
            f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('flashcard.ipa')}{ui.S.RESET}       {ui.S.FG.CYAN}{word.get('ipa', 'N/A')}{ui.S.RESET}",
        ]
        ui.box(word["word"], lines)

        ui.wait()

        lines = [
            f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('flashcard.word')}{ui.S.RESET}      {ui.S.FG.YELLOW}{word['word'].upper()}{ui.S.RESET}",
            f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('flashcard.ipa')}{ui.S.RESET}       {ui.S.FG.CYAN}{word.get('ipa', 'N/A')}{ui.S.RESET}",
            f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('flashcard.meaning')}{ui.S.RESET}   {ui.S.FG.GREEN}{word['meaning']}{ui.S.RESET}",
            f"{ui.S.BOLD}{ui.S.FG.WHITE}Definition{ui.S.RESET}{ui.S.FG.CYAN}  {word.get('definition', '')}{ui.S.RESET}",
            f"                          {ui.S.FG.GREEN}{word.get('definition_vi', '')}{ui.S.RESET}",
            f"{ui.S.BOLD}{ui.S.FG.WHITE}{lang.t('flashcard.example')}{ui.S.RESET}   {ui.S.FG.BRIGHT_BLACK}{word.get('example', 'N/A')}{ui.S.RESET}",
            f"                          {ui.S.FG.GREEN}{word.get('example_vi', '')}{ui.S.RESET}",
        ]
        ui.box(word["word"], lines)

        while True:
            choice = ui.input_prompt(lang.t("flashcard.prompt")).lower()
            if not choice:
                choice = "y"
            if choice in ("y", "n"):
                break
            ui.warn(lang.t("flashcard.invalid"))

        if choice == "y":
            update_after_review(word["id"], True)
            correct_count += 1
            ui.success(lang.t("flashcard.yes"))
        else:
            update_after_review(word["id"], False)
            ui.info(lang.t("flashcard.no"))

        ui.wait()

    ui.clear()
    ui.header(lang.t("flashcard.complete"))
    show_stats()

    pct = int(correct_count / total * 100) if total else 0
    if pct >= 80:
        ui.success(lang.t("flashcard.excellent", c=correct_count, t=total, p=pct))
    elif pct >= 50:
        ui.info(lang.t("flashcard.good", c=correct_count, t=total, p=pct))
    else:
        ui.warn(lang.t("flashcard.keep", c=correct_count, t=total, p=pct))

    ui.wait()
