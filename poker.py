#!/usr/bin/env python3
"""Покерный тренажёр: все разновидности в одном месте.

    python3 poker.py                     меню: выбрать разновидность
    python3 poker.py start               с чего начать, если вы с нуля
    python3 poker.py list                список разновидностей
    python3 poker.py terms               словарь терминов (содержание)
    python3 poker.py terms аутсы         объяснить один термин
    python3 poker.py terms --all         весь словарь целиком
    python3 poker.py terms --group Математика
    python3 poker.py terms --markdown    пересобрать GLOSSARY.md
    python3 poker.py test                самопроверка всех расчётов

    python3 poker.py holdem equity AhKh --board Kh7h2c --vs KsQd
    python3 poker.py omaha lesson 1
    python3 poker.py razz quiz showdown

Любую разновидность можно запускать и напрямую — у каждой свой
калькулятор в своей папке:

    python3 texas_holdem/equity_calculator.py
    python3 omaha/equity_calculator.py

Это обучающая программа. Она не подключается ни к одному покер-руму
и ничего не считывает с экрана: подсказчики во время игры запрещены
правилами всех легальных румов. Тренажёр — для работы между сессиями.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import glossary, ui

# Разновидности в порядке, в котором их осмысленно изучать.
# Короткие имена — чтобы не печатать seven_card_stud целиком.
VARIANTS: List[Tuple[str, Sequence[str]]] = [
    ("texas_holdem", ("holdem", "nlhe", "холдем")),
    ("omaha", ("plo", "омаха")),
    ("omaha_hi_lo", ("o8", "hilo", "хайлоу")),
    ("short_deck", ("shortdeck", "6plus", "шортдек")),
    ("five_card_draw", ("draw", "дро")),
    ("seven_card_stud", ("stud", "стад")),
    ("razz", ("разз",)),
    ("deuce_to_seven", ("27", "2-7", "triple", "лоуболл")),
    ("badugi", ("бадуги",)),
]

ALIASES = {}
for _key, _names in VARIANTS:
    ALIASES[_key] = _key
    for _name in _names:
        ALIASES[_name] = _key


def load(key: str):
    """Возвращает (описание правил, модуль уроков, функция запуска)."""
    rules = importlib.import_module("%s.rules" % key)
    lessons = importlib.import_module("%s.lessons" % key)
    calculator = importlib.import_module("%s.equity_calculator" % key)
    return rules.VARIANT, lessons, calculator


def list_variants() -> None:
    ui.title("Разновидности покера в этом проекте")
    ui.para("""
        Папки идут в том порядке, в котором их осмысленно изучать.
        У каждой свой калькулятор equity и свои уроки.
    """)
    print()
    for key, names in VARIANTS:
        variant = importlib.import_module("%s.rules" % key).VARIANT
        print("  %s%s%s" % (ui.BOLD, variant.name, ui.RESET))
        ui.para(variant.short_description, indent=6)
        details = "карт на руках: %d   общих карт: %d   колода: %d" % (
            variant.hole_size, variant.board_size, len(variant.deck()))
        print(ui.color("      %s" % details, ui.DIM))
        print(ui.color("      папка: %s/   короткое имя: %s"
                       % (key, names[0] if names else key), ui.DIM))
        print()


def start_here() -> None:
    ui.title("С чего начать, если вы в покере с нуля")
    ui.para("""
        Коротко: начните с техасского холдема и не трогайте остальные
        разновидности, пока не освоите его. Правила у всех игр разные,
        но считать equity, аутсы и пот-оддсы вы научитесь один раз
        и будете применять везде.
    """)

    ui.section("Шаг 1. Словарь")
    ui.block("""
        python3 poker.py terms
    """)
    ui.para("""
        Прочитайте группы «Основы», «Карты и борд» и «Комбинации».
        Без этих слов дальше будет непонятно.
    """, indent=4)

    ui.section("Шаг 2. Холдем: правила и комбинации")
    ui.block("""
        python3 poker.py holdem lesson 1
        python3 poker.py holdem lesson 2
        python3 poker.py holdem quiz combos
    """)
    ui.para("""
        Квиз на комбинации повторяйте по пять минут несколько дней,
        пока узнавание не станет мгновенным. Пока вы думаете
        над комбинацией, думать над игрой нечем.
    """, indent=4)

    ui.section("Шаг 3. Математика")
    ui.block("""
        python3 poker.py holdem lesson 3     equity
        python3 poker.py holdem lesson 4     аутсы и правило 2 и 4
        python3 poker.py holdem lesson 5     пот-оддсы
        python3 poker.py holdem drill        колл или фолд
    """)
    ui.para("""
        Тренажёр «колл или фолд» — самое полезное упражнение
        во всём проекте.
    """, indent=4)

    ui.section("Шаг 4. Стартовые руки и ошибки")
    ui.block("""
        python3 poker.py holdem lesson 6
        python3 poker.py holdem lesson 7
        python3 poker.py holdem preflop
    """)

    ui.section("Шаг 5. Только потом — другие разновидности")
    ui.para("""
        Дальше берите по одной. Омаха ближе всего к холдему,
        пятикарточный дро проще всех по правилам, разз и бадуги
        переворачивают привычную логику. Список:
    """)
    ui.block("""
        python3 poker.py list
    """)
    ui.hint("Играйте при этом только на условные фишки, пока уроки "
            "не закончатся: на бесплатных столах ошибки ничего "
            "не стоят.")


def variants_menu() -> None:
    ui.title("Покерный тренажёр")
    ui.para("""
        Выберите разновидность. Если вы в покере с нуля — выберите
        пункт 0: там написано, с чего начинать.
    """)
    while True:
        ui.section("Разновидности")
        print("  0. С чего начать (если вы новичок)")
        for index, (key, _names) in enumerate(VARIANTS, start=1):
            variant = importlib.import_module("%s.rules" % key).VARIANT
            print("  %d. %-26s %s" % (index, variant.name,
                                      ui.color(variant.short_description[:34],
                                               ui.DIM)))
        print("  t. Словарь терминов")
        print("  q. Выход")
        choice = ui.ask("Выбор").lower()
        if choice in ("q", ""):
            print()
            return
        if choice == "0":
            start_here()
            ui.pause()
            continue
        if choice == "t":
            glossary.print_contents()
            ui.pause()
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(VARIANTS):
            key = VARIANTS[int(choice) - 1][0]
            variant, lessons, calculator = load(key)
            calculator.main([])
            continue
        ui.bad("Нет такого пункта.")


def terms_command(argv: Sequence[str]) -> int:
    if not argv:
        glossary.print_contents()
        return 0
    if argv[0] == "--all":
        glossary.print_all()
        return 0
    if argv[0] == "--markdown":
        # Этим собирается GLOSSARY.md: python3 poker.py terms --markdown > GLOSSARY.md
        sys.stdout.write(glossary.markdown())
        return 0
    if argv[0] == "--group":
        if len(argv) < 2:
            ui.bad("Укажите группу, например: terms --group Математика")
            return 1
        name = " ".join(argv[1:])
        matches = [group for group in glossary.GROUPS
                   if name.lower() in group.lower()]
        if not matches:
            ui.bad("Группы «%s» нет. Доступные: %s"
                   % (name, ", ".join(glossary.GROUPS)))
            return 1
        for group in matches:
            glossary.print_group(group)
        return 0

    query = " ".join(argv)
    found = glossary.find(query)
    if not found:
        ui.bad("Термина «%s» в словаре нет." % query)
        ui.hint("Посмотреть содержание: python3 poker.py terms")
        return 1
    ui.title("Словарь: «%s»" % query)
    for term in found[:12]:
        glossary.print_term(term)
    if len(found) > 12:
        print()
        ui.hint("Найдено ещё %d терминов — уточните запрос." % (len(found) - 12))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv:
        variants_menu()
        return 0

    first = argv[0].lower()

    if first in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if first == "list":
        list_variants()
        return 0
    if first == "start":
        start_here()
        return 0
    if first == "terms":
        return terms_command(argv[1:])
    if first == "test":
        import selftest
        return selftest.run()

    key = ALIASES.get(first)
    if key is None:
        ui.bad("Не знаю разновидности «%s»." % argv[0])
        ui.hint("Список: python3 poker.py list")
        return 1

    _variant, _lessons, calculator = load(key)
    return calculator.main(argv[1:])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
        raise SystemExit(130)
