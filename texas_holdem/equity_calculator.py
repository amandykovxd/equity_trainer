#!/usr/bin/env python3
"""Калькулятор equity и тренажёр для техасского холдема.

Запуск без аргументов — меню (с него и начинайте, если вы новичок):

    python3 texas_holdem/equity_calculator.py

Прямые команды:

    equity 9h8h --board Kh7h2c --vs KsQd --pot 100 --bet 50
    equity AsAh --opponents 5          # против 5 случайных рук
    hand AsKsQhJhTd                    # что это за комбинация
    lesson 2                           # урок про комбинации
    quiz combos                        # квиз на узнавание комбинаций
    quiz showdown                      # кто выиграл банк
    drill                              # колл или фолд
    chart                              # таблица 169 стартовых рук
    outs                               # квиз на счёт аутсов
    preflop                            # квиз на стартовые руки
    terms                              # термины холдема

Это обучающая программа. Она не подключается ни к одному покер-руму
и ничего не считывает с экрана: подсказчики во время игры запрещены
правилами румов. Тренажёр — для работы между сессиями.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ui
from core.cli import Extra, run
from texas_holdem import drills as holdem_drills
from texas_holdem import lessons
from texas_holdem.rules import VARIANT


def extras():
    """Команды, которые есть только у холдема."""
    return [
        Extra("chart", "Таблица стартовых рук", lessons.print_chart),
        Extra("outs", "Квиз: посчитай аутсы", holdem_drills.quiz_outs),
        Extra("preflop", "Квиз: стартовые руки", holdem_drills.quiz_preflop),
    ]


def main(argv=None) -> int:
    return run(VARIANT, lessons, argv, extras())


if __name__ == "__main__":
    raise SystemExit(main())
