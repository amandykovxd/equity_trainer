#!/usr/bin/env python3
"""Калькулятор equity и тренажёр: Семикарточный стад.

Общих карт нет: у каждого свои 7 карт, часть из них открыта для всех.

Запуск без аргументов — меню:

    python3 seven_card_stud/equity_calculator.py

Прямые команды:

    equity AsAhKd7c --vs KsKhQdJc9s
    equity AsAh7h --opponents 2
    hand AsAhKd7c7h2s9d

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
from seven_card_stud import lessons
from seven_card_stud.rules import VARIANT


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv)


if __name__ == "__main__":
    raise SystemExit(main())
