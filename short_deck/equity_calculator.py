#!/usr/bin/env python3
"""Калькулятор equity и тренажёр: Шортдек-холдем.

Холдем на 36 картах, где флеш сильнее фулл-хауса, а тройка сильнее стрита.

Запуск без аргументов — меню:

    python3 short_deck/equity_calculator.py

Прямые команды:

    equity AsAh --board Kh9h7c --vs KsQd --pot 100 --bet 50
    equity AsKs --opponents 4
    hand AhKh9h7h6h

    lesson              список уроков (lesson 1, lesson all)
    quiz showdown       кто выиграл банк
    quiz combos         назови комбинацию
    drill               колл или фолд
    terms               термины этой игры

Это обучающая программа. Она не подключается ни к одному покер-руму
и ничего не считывает с экрана: подсказчики во время игры запрещены
правилами румов. Тренажёр — для работы между сессиями.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cli import run
from short_deck import lessons
from short_deck.rules import VARIANT


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv)


if __name__ == "__main__":
    raise SystemExit(main())
