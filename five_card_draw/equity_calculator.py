#!/usr/bin/env python3
"""Калькулятор equity и тренажёр: Пятикарточный дро.

5 закрытых карт и замена; общих карт нет — самые простые правила.

Запуск без аргументов — меню:

    python3 five_card_draw/equity_calculator.py

Прямые команды:

    equity 9s9h --vs QsQd7c4h2s
    equity AsKsQsJsTs --opponents 3
    hand AsAhKd7c7h

    lesson              список уроков (lesson 1, lesson all)
    quiz showdown       кто выиграл банк
    quiz combos         назови комбинацию
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
from five_card_draw import lessons
from five_card_draw.rules import VARIANT


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv)


if __name__ == "__main__":
    raise SystemExit(main())
