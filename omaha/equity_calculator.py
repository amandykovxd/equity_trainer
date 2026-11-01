#!/usr/bin/env python3
"""Калькулятор equity и тренажёр: Омаха (PLO).

4 своих карты, 5 общих, в комбинации — ровно 2 своих и ровно 3 общих.

Запуск без аргументов — меню:

    python3 omaha/equity_calculator.py

Прямые команды:

    equity AsAhKsKh --board Qh7h2d --vs 9s8d7c6c --pot 100 --bet 60
    equity AsAhKsKh --opponents 3
    hand AsAhKsKh Qh7h2d9dKc

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
from omaha import lessons
from omaha.rules import VARIANT


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv)


if __name__ == "__main__":
    raise SystemExit(main())
