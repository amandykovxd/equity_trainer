"""Мелкие помощники для вывода в терминал."""
from __future__ import annotations

import re
import sys
import textwrap
from typing import Optional

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"

WIDTH = 72


ANSI_PATTERN = re.compile(r"\033\[[0-9;]*m")


def color(text: str, code: str) -> str:
    return code + text + RESET


def visible_length(text: str) -> int:
    """Длина строки на экране: управляющие последовательности не считаются."""
    return len(ANSI_PATTERN.sub("", text))


def pad(text: str, width: int) -> str:
    """Дополняет строку пробелами до нужной ВИДИМОЙ ширины.

    Обычный %-18s здесь не годится: в раскрашенных картах половина
    символов — это управляющие коды, которых на экране не видно.
    """
    return text + " " * max(0, width - visible_length(text))


def title(text: str) -> None:
    print()
    print(color("=" * WIDTH, CYAN))
    print(color("  " + text, BOLD + CYAN))
    print(color("=" * WIDTH, CYAN))


def section(text: str) -> None:
    print()
    print(color(text, BOLD))
    print(color("-" * min(WIDTH, len(text) + 2), DIM))


def para(text: str, indent: int = 2) -> None:
    """Печатает абзац, сам расставляя переносы по ширине терминала.

    Переносы строк в исходном тексте значения не имеют: абзацы
    разделяются пустой строкой, всё остальное склеивается и
    переносится заново.
    """
    pad = " " * indent
    body = textwrap.dedent(text.strip("\n"))
    chunks = [" ".join(chunk.split()) for chunk in body.split("\n\n")]
    for index, chunk in enumerate(filter(None, chunks)):
        if index:
            print()
        print(textwrap.fill(chunk, width=WIDTH,
                            initial_indent=pad, subsequent_indent=pad))


def block(text: str, indent: int = 2) -> None:
    """Печатает текст как есть, сохраняя выравнивание столбиков."""
    pad = " " * indent
    lines = textwrap.dedent(text.strip("\n")).split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    for line in lines:
        print(pad + line if line.strip() else "")


def item(number: str, text: str, indent: int = 2) -> None:
    """Пункт нумерованного списка с «висячим» отступом."""
    pad = " " * indent
    prefix = pad + number + " "
    print(textwrap.fill(" ".join(text.split()), width=WIDTH,
                        initial_indent=prefix,
                        subsequent_indent=" " * len(prefix)))


def _marked(mark: str, text: str, code: str) -> None:
    """Строка с пометкой слева, с переносом под текст, а не под пометку."""
    prefix = "  " + mark + " "
    body = textwrap.fill(" ".join(text.split()), width=WIDTH,
                         initial_indent=prefix,
                         subsequent_indent=" " * len(prefix))
    print(color(body, code))


def good(text: str) -> None:
    _marked("\u2713", text, GREEN)


def bad(text: str) -> None:
    _marked("\u2717", text, RED)


def hint(text: str) -> None:
    print()
    _marked("\u2192", text, YELLOW)


def pause(message: str = "Enter — дальше") -> None:
    if sys.stdin.isatty():
        try:
            input(color("\n  [%s]" % message, DIM))
        except EOFError:
            pass


def ask(prompt: str, default: Optional[str] = None) -> str:
    """Спрашивает строку. Ctrl-D / Ctrl-C трактуются как «выход»."""
    suffix = (" [%s]" % default) if default else ""
    try:
        answer = input(color("  " + prompt + suffix + ": ", BOLD)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)
    return answer or (default or "")


def ask_choice(prompt: str, choices: str) -> str:
    """Спрашивает один символ из набора, пока не получит корректный."""
    while True:
        answer = ask("%s (%s)" % (prompt, "/".join(choices))).lower()
        if answer[:1] in choices:
            return answer[:1]
        bad("Ответ должен быть одним из: %s" % ", ".join(choices))


def bar(fraction: float, width: int = 30) -> str:
    """Полоска-индикатор: наглядно показывает проценты."""
    filled = int(round(max(0.0, min(1.0, fraction)) * width))
    code = GREEN if fraction >= 0.5 else (YELLOW if fraction >= 0.3 else RED)
    return color("█" * filled, code) + color("░" * (width - filled), DIM)
