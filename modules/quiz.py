import random
from modules import ui, lang
from modules.utils import load_words, get_next_review_words, update_after_review


def run():
    words = get_next_review_words(limit=15)
    if len(words) < 4:
        words = load_words()

    if len(words) < 4:
        ui.error(lang.t("quiz.empty"))
        ui.wait()
        return

    random.shuffle(words)
    selected = words[:10]
    total = len(selected)
    score = 0

    ui.clear()
    ui.header(lang.t("quiz.header"), lang.t("quiz.subtitle", n=total))

    for i, word in enumerate(selected, 1):
        ui.clear()
        ui.header(lang.t("quiz.question", i=i, total=total))

        options = [word["meaning"]]
        pool = [w for w in words if w["id"] != word["id"]]
        distractors = random.sample(pool, min(3, len(pool)))
        for d in distractors:
            options.append(d["meaning"])
        random.shuffle(options)

        q_lines = [
            f"  {ui.S.BOLD}{ui.S.FG.YELLOW}{lang.t('quiz.what_is')}{ui.S.RESET}",
            f"  {ui.S.BOLD}{ui.S.FG.WHITE}{word['word'].upper()}{ui.S.RESET}",
            f"  {ui.S.FG.BRIGHT_BLACK}{word.get('ipa', '')}{ui.S.RESET}",
            "",
        ]
        for j, opt in enumerate(options, 1):
            q_lines.append(f"  {ui.S.FG.CYAN}[{j}]{ui.S.RESET} {opt}")

        ui.box(lang.t("quiz.question", i=i, total=total), q_lines)

        while True:
            try:
                ans = ui.input_prompt(lang.t("quiz.prompt", n=len(options)))
                answer = int(ans)
                if 1 <= answer <= len(options):
                    break
            except ValueError:
                pass
            ui.warn(lang.t("quiz.invalid", n=len(options)))

        correct = options[answer - 1] == word["meaning"]
        if correct:
            score += 1
            update_after_review(word["id"], True)
        else:
            update_after_review(word["id"], False)

        ui.clear()
        ui.header(lang.t("quiz.question", i=i, total=total), lang.t("quiz.result_header"))

        if correct:
            result_lines = [
                f"  {ui.S.FG.GREEN}{ui.S.BOLD}\u2714 {lang.t('quiz.correct')}{ui.S.RESET}",
                "",
                f"  {ui.S.BOLD}{lang.t('quiz.word')}{ui.S.RESET}  {ui.S.FG.YELLOW}{word['word']}{ui.S.RESET}",
                f"  {ui.S.BOLD}{lang.t('quiz.meaning')}{ui.S.RESET} {ui.S.FG.GREEN}{word['meaning']}{ui.S.RESET}",
            ]
        else:
            correct_opt = options.index(word["meaning"]) + 1
            result_lines = [
                f"  {ui.S.FG.RED}{ui.S.BOLD}\u2718 {lang.t('quiz.wrong')}{ui.S.RESET}",
                "",
                f"  {ui.S.BOLD}{lang.t('quiz.word')}{ui.S.RESET}  {ui.S.FG.YELLOW}{word['word']}{ui.S.RESET}",
                f"  {ui.S.BOLD}{lang.t('quiz.meaning')}{ui.S.RESET} {ui.S.FG.GREEN}{word['meaning']}{ui.S.RESET}",
                f"  {ui.S.BOLD}{lang.t('quiz.your_answer')}{ui.S.RESET}  {ui.S.FG.RED}{options[answer - 1]}{ui.S.RESET}",
            ]

        if word.get("example"):
            result_lines.append(f"  {ui.S.BOLD}{lang.t('quiz.example')}{ui.S.RESET}   {ui.S.FG.BRIGHT_BLACK}{word['example']}{ui.S.RESET}")

        bar = ui.progress_bar(score, i)
        result_lines.extend(["", f"  {lang.t('quiz.score')} {score}/{i}  {bar}"])
        ui.box(lang.t("quiz.result_header"), result_lines)

        if i < total:
            ui.wait()

    ui.clear()
    ui.header(lang.t("quiz.complete"))

    pct = int(score / total * 100)

    if pct >= 80:
        msg = f"{ui.S.FG.GREEN}{ui.S.BOLD}{lang.t('quiz.excellent')}{ui.S.RESET}"
    elif pct >= 60:
        msg = f"{ui.S.FG.CYAN}{ui.S.BOLD}{lang.t('quiz.good')}{ui.S.RESET}"
    elif pct >= 40:
        msg = f"{ui.S.FG.YELLOW}{ui.S.BOLD}{lang.t('quiz.trying')}{ui.S.RESET}"
    else:
        msg = f"{ui.S.FG.RED}{ui.S.BOLD}{lang.t('quiz.study')}{ui.S.RESET}"

    bar = ui.progress_bar(score, total, 25)
    summary = [
        f"  {msg}",
        "",
        f"  {ui.S.BOLD}{lang.t('quiz.final_score')}{ui.S.RESET}  {score}/{total}",
        f"  {ui.S.BOLD}{lang.t('quiz.percentage')}{ui.S.RESET}  {pct}%",
        "",
        f"  {bar}",
    ]
    ui.box(lang.t("quiz.complete"), summary)
    ui.wait()
