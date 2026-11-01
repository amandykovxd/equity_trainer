#!/usr/bin/env python3
"""Калькулятор equity и тренажёр: Омаха хай-лоу (Omaha/8).

Омаха, где банк делится между сильнейшей рукой и слабейшей (если лоу вообще собралось).

Запуск без аргументов — меню:

    python3 omaha_hi_lo/equity_calculator.py

Прямые команды:

    equity As2d3h4c --board 5h6c7s --vs KsKhQdJc
    equity As2dKsQh --opponents 2

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
from omaha_hi_lo import lessons
from omaha_hi_lo.rules import VARIANT


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv)


if __name__ == "__main__":
    raise SystemExit(main())
