#!/usr/bin/env python3
"""Калькулятор equity и тренажёр: Разз.

Стад, где побеждает самая слабая рука; лучшая рука — 5-4-3-2-a.

Запуск без аргументов — меню:

    python3 razz/equity_calculator.py

Прямые команды:

    equity As2d3h --vs 5s6d7h
    equity As2d3h4c5s6h --vs 8s7d6c5h4d3s2h
    hand As2d3h4c5s7h8d

    lesson              список уроков (lesson 1, lesson all)
    quiz showdown       кто выиграл банк
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
from razz import lessons
from razz.rules import VARIANT


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv)


if __name__ == "__main__":
    raise SystemExit(main())
