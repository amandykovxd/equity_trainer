#!/usr/bin/env python3
"""Старая точка входа. Проект вырос, и теперь вход общий — poker.py.

Раньше здесь был тренажёр только по техасскому холдему. Сейчас
разновидностей девять, у каждой своя папка и свой калькулятор:

    python3 poker.py                            меню со всеми играми
    python3 poker.py start                      с чего начать с нуля
    python3 texas_holdem/equity_calculator.py   то, что было здесь

Этот файл просто передаёт аргументы в poker.py, чтобы старые команды
не ломались: «python3 trainer.py lesson 2» по-прежнему откроет урок
холдема.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    from core import ui
    import poker

    argv = sys.argv[1:]
    # Без аргументов показываем общее меню, с аргументами — считаем,
    # что речь про холдем, как было раньше.
    if not argv:
        ui.hint("trainer.py теперь только перенаправляет: разновидностей девять, "
                "общий вход — poker.py. Открываю общее меню.")
        return poker.main([])
    ui.hint("Команды холдема переехали в texas_holdem/equity_calculator.py "
            "(или «python3 poker.py holdem ...»). Выполняю как холдем.")
    return poker.main(["holdem"] + argv)


if __name__ == "__main__":
    raise SystemExit(main())
