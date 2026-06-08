import os
import sys
import time
import shutil
import re


if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

USE_UNICODE = sys.stdout.encoding.lower() in ("utf-8", "utf8")

if USE_UNICODE:
    H = "\u2500"
    V = "\u2502"
    TL = "\u250c"
    TR = "\u2510"
    BL = "\u2514"
    BR = "\u2518"
    LT = "\u251c"
    RT = "\u2524"
    H2 = "\u2550"
    V2 = "\u2551"
    TL2 = "\u2554"
    TR2 = "\u2557"
    BL2 = "\u255a"
    BR2 = "\u255d"
    LT2 = "\u2560"
    RT2 = "\u2563"
else:
    H = "="
    V = "|"
    TL = "+"
    TR = "+"
    BL = "+"
    BR = "+"
    LT = "+"
    RT = "+"
    H2 = "="
    V2 = "|"
    TL2 = "+"
    TR2 = "+"
    BL2 = "+"
    BR2 = "+"
    LT2 = "+"
    RT2 = "+"

BAR_FILL = "\u2588" if USE_UNICODE else "#"
BAR_EMPTY = "\u2591" if USE_UNICODE else "-"
CHECK = "\u2714" if USE_UNICODE else "V"
CROSS = "\u2718" if USE_UNICODE else "X"
INFO = "\u2139" if USE_UNICODE else "i"
WARN = "\u26a0" if USE_UNICODE else "!"
ARROW = "\u276f" if USE_UNICODE else ">>"

SPIN_CHARS = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]
if not USE_UNICODE:
    SPIN_CHARS = ["|", "/", "-", "\\"]

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    class FG:
        BLACK = "\033[30m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"
        BRIGHT_BLACK = "\033[90m"
        BRIGHT_RED = "\033[91m"
        BRIGHT_GREEN = "\033[92m"
        BRIGHT_YELLOW = "\033[93m"
        BRIGHT_BLUE = "\033[94m"
        BRIGHT_MAGENTA = "\033[95m"
        BRIGHT_CYAN = "\033[96m"
        BRIGHT_WHITE = "\033[97m"

    class BG:
        BLACK = "\033[40m"
        RED = "\033[41m"
        GREEN = "\033[42m"
        YELLOW = "\033[43m"
        BLUE = "\033[44m"
        MAGENTA = "\033[45m"
        CYAN = "\033[46m"
        WHITE = "\033[47m"
        BRIGHT_BLACK = "\033[100m"
        BRIGHT_RED = "\033[101m"
        BRIGHT_GREEN = "\033[102m"
        BRIGHT_YELLOW = "\033[103m"
        BRIGHT_BLUE = "\033[104m"


S = Style


def init():
    if os.name == "nt":
        os.system("")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def term_width():
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


def cprint(text, style="", end="\n"):
    try:
        print(f"{style}{text}{S.RESET}", end=end)
    except UnicodeEncodeError:
        safe = text.encode("ascii", errors="replace").decode("ascii")
        print(f"{style}{safe}{S.RESET}", end=end)


def strip_ansi(text):
    return _ANSI_RE.sub("", text)


def visible_len(text):
    plain = strip_ansi(text)
    length = 0
    for ch in plain:
        if ord(ch) > 0x2E80:
            length += 2
        else:
            length += 1
    return length


def pad_right(text, width):
    vlen = visible_len(text)
    return text + " " * max(0, width - vlen)


def center_text(text, width):
    vlen = visible_len(text)
    if vlen >= width:
        return text
    left = (width - vlen) // 2
    return " " * left + text


def _parse_styled_segments(text):
    segments = []
    current_style = ""
    pos = 0
    while pos < len(text):
        m = _ANSI_RE.match(text, pos)
        if m:
            code = m.group()
            if code == S.RESET:
                current_style = ""
            else:
                current_style += code
            pos = m.end()
        else:
            n = _ANSI_RE.search(text, pos)
            end = n.start() if n else len(text)
            plain = text[pos:end]
            if plain:
                segments.append((current_style, plain))
            pos = end
    return segments


def word_wrap(text, max_width, indent=0):
    text = str(text)
    vlen = visible_len(text)
    if vlen <= max_width:
        return [text]

    segments = _parse_styled_segments(text)

    wrapped_plain = []
    cur = ""
    for _, seg_text in segments:
        for w in seg_text.split():
            test = (cur + " " + w).strip()
            if visible_len(test) <= max_width:
                cur = test
            else:
                if cur:
                    wrapped_plain.append(cur)
                cur = w
    if cur:
        wrapped_plain.append(cur)

    if len(wrapped_plain) <= 1:
        return [text]

    all_words = strip_ansi(text).split()
    keep_count = len(wrapped_plain[0].split())

    if keep_count < len(all_words):
        keep_words = all_words[:keep_count]
        pos = 0
        ki = 0
        while ki < len(keep_words) and pos < len(text):
            if text[pos] == "\033":
                pos += 1
                while pos < len(text) and text[pos] != "m":
                    pos += 1
                if pos < len(text):
                    pos += 1
            elif text[pos] == " ":
                pos += 1
            else:
                w = keep_words[ki]
                if text[pos:pos + len(w)] == w:
                    pos += len(w)
                    ki += 1
                else:
                    pos += 1
        first_styled = text[:pos] + S.RESET
    else:
        first_styled = text

    if not first_styled:
        first_styled = text

    content_style = ""
    auto_indent = 0
    pos = 0
    for seg_style, seg_text in segments:
        if seg_style:
            content_style = seg_style
            auto_indent = pos
        pos += len(seg_text)

    if not indent:
        indent = auto_indent

    result = [first_styled]
    for line in wrapped_plain[1:]:
        padded = " " * indent + line if indent else line
        result.append((content_style + padded + S.RESET) if content_style else padded)

    return result


def banner():
    w = min(term_width(), 62)
    inner = w - 4

    from modules import lang
    title = lang.t("app.title")
    subtitle = lang.t("app.subtitle")
    tagline = lang.t("app.tagline")

    rainbow = [
        S.FG.BRIGHT_RED,
        S.FG.BRIGHT_YELLOW,
        S.FG.BRIGHT_GREEN,
        S.FG.BRIGHT_CYAN,
        S.FG.BRIGHT_BLUE,
        S.FG.BRIGHT_MAGENTA,
    ]

    print()
    cprint(f"  {TL2}{H2 * inner}{TR2}", S.FG.CYAN + S.BOLD)

    art_lines = [
        "███████╗███╗   ██╗ ██████╗ ██╗     ██╗███████╗",
        "██╔════╝████╗  ██║██╔════╝ ██║     ██║██╔════╝",
        "█████╗  ██╔██╗ ██║██║  ███╗██║     ██║█████╗",
        "██╔══╝  ██║╚██╗██║██║   ██║██║     ██║██╔══╝",
        "███████╗██║ ╚████║╚██████╔╝███████╗██║███████╗",
        "╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝╚══════╝",
    ]

    for i, line in enumerate(art_lines):
        cprint(f"  {V2} {pad_right(center_text(line, inner), inner)} {V2}", rainbow[i] + S.BOLD)

    cprint(f"  {LT2}{H2 * inner}{RT2}", S.FG.CYAN + S.BOLD)

    rail = S.FG.CYAN
    rainbow_title = ""
    rainbow_word = "ENGLISH"
    for j, ch in enumerate(rainbow_word):
        rainbow_title += S.BOLD + rainbow[j % len(rainbow)] + ch + S.RESET
    rainbow_title += "  " + S.BOLD + S.FG.YELLOW + "Learning Tool" + S.RESET
    cprint(f"{rail}  {V2} {pad_right(center_text(rainbow_title, inner), inner)} {V2}{S.RESET}")

    cprint(f"{rail}  {V2} {pad_right(center_text(subtitle, inner), inner)} {V2}{S.RESET}")
    cprint(f"  {LT2}{H2 * inner}{RT2}", S.FG.CYAN + S.BOLD)
    cprint(f"  {V2} {pad_right(center_text(tagline, inner), inner)} {V2}", S.FG.GREEN)
    cprint(f"  {BL2}{H2 * inner}{BR2}", S.FG.CYAN + S.BOLD)
    print()


def _box_render_lines(lines, inner):
    for line in lines:
        raw = str(line)
        wrapped = word_wrap(raw, inner)
        for wl in wrapped:
            cprint(f"  {V2} {pad_right(wl, inner)} {V2}", S.FG.CYAN)


def box(title, content_lines):
    w = min(term_width(), 62)
    inner = w - 4

    cprint(f"  {TL2}{H2 * inner}{TR2}", S.FG.CYAN + S.BOLD)
    if title:
        cprint(f"  {V2} {pad_right(center_text(title, inner), inner)} {V2}", S.FG.CYAN)
        cprint(f"  {LT2}{H2 * inner}{RT2}", S.FG.CYAN + S.BOLD)
    _box_render_lines(content_lines, inner)
    cprint(f"  {BL2}{H2 * inner}{BR2}", S.FG.CYAN + S.BOLD)
    print()


def progress_bar(current, total, width=20):
    if total == 0:
        return ""
    filled = int(current / total * width)
    bar = BAR_FILL * filled + BAR_EMPTY * (width - filled)
    pct = int(current / total * 100)
    return f"{S.FG.GREEN}{bar}{S.RESET}  {pct}%"


def header(text, sub=""):
    w = min(term_width(), 62)
    inner = w - 4
    print()
    cprint(f"  {TL2}{H2 * inner}{TR2}", S.FG.CYAN + S.BOLD)

    lines = word_wrap(text, inner)
    for l in lines:
        cprint(f"  {V2} {pad_right(f'{S.BOLD}{S.FG.YELLOW}{l}', inner)} {V2}", S.FG.CYAN + S.BOLD)

    if sub:
        sub_lines = word_wrap(sub, inner)
        for l in sub_lines:
            cprint(f"  {V2} {pad_right(f'{S.FG.BRIGHT_BLACK}{l}', inner)} {V2}", S.FG.CYAN)

    cprint(f"  {BL2}{H2 * inner}{BR2}", S.FG.CYAN + S.BOLD)
    print()


def separator():
    w = min(term_width(), 62)
    inner = w - 4
    cprint(f"  {LT2}{H2 * inner}{RT2}", S.FG.BRIGHT_BLACK)


def menu_option(num, title, desc=""):
    cprint(f"  {S.BOLD}{S.FG.CYAN}[{num}]{S.RESET} {S.BOLD}{title}{S.RESET}", end="")
    if desc:
        cprint(f"  {S.FG.BRIGHT_BLACK}{desc}{S.RESET}")
    else:
        print()


def input_prompt(prompt):
    try:
        val = input(f"  {S.BOLD}{S.FG.YELLOW}{ARROW}{S.RESET} {prompt}{S.FG.CYAN} ")
        print(S.RESET, end="")
        return val.strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def confirm(prompt):
    from modules import lang
    while True:
        val = input_prompt(f"{prompt} ({lang.t('ui.yes')}/{lang.t('ui.no')})").lower()
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False


def wait():
    from modules import lang
    try:
        input(f"  {S.FG.BRIGHT_BLACK}{lang.t('ui.wait')}{S.RESET}")
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def success(text):
    cprint(f"  {S.FG.GREEN}{CHECK} {text}{S.RESET}")


def error(text):
    cprint(f"  {S.FG.RED}{CROSS} {text}{S.RESET}")


def info(text):
    cprint(f"  {S.FG.BRIGHT_BLACK}{INFO} {text}{S.RESET}")


def warn(text):
    cprint(f"  {S.FG.YELLOW}{WARN} {text}{S.RESET}")


def spin(message="Loading"):
    for _ in range(8):
        for frame in SPIN_CHARS:
            sys.stdout.write(f"\r  {S.FG.CYAN}{frame}{S.RESET} {message}...")
            sys.stdout.flush()
            time.sleep(0.05)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()
