#!/usr/bin/env python3
"""Калькулятор equity и тренажёр: Бадуги.

4 карты, побеждает самая низкая рука из карт разных мастей и разных достоинств; лучшая — 4-3-2-a.

Запуск без аргументов — меню:

    python3 badugi/equity_calculator.py

Прямые команды:

    equity 4s3h2dAc --vs 7s5h3d2c
    equity 5s3h2d --opponents 2
    hand 4s3h2d2c

    lesson              список уроков (lesson 1, lesson all)
    quiz showdown       кто выиграл банк
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
from badugi import lessons
from badugi.rules import VARIANT


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv)


if __name__ == "__main__":
    raise SystemExit(main())
