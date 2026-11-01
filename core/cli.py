"""Командная строка и меню, общие для всех разновидностей.

Каждая разновидность получает одинаковый набор команд (equity, hand,
lesson, quiz, drill, terms) и может добавить свои — например, у холдема
есть таблица стартовых рук, которой больше нигде нет.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from . import drills, glossary, ui
from .calculator import analyze
from .cards import BadCard, Card, parse_cards, pretty
from .variant import SPLIT, Variant


@dataclass
class Extra:
    """Дополнительная команда, своя у конкретной разновидности."""
    key: str
    title: str
    action: Callable[[], None]


def card_help(variant: Variant) -> None:
    ui.para("""
        Карты вводятся как номинал + масть: As = туз пик, Th или 10h =
        десятка червей, 7d = семёрка бубен.
        Масти: s ♠ пики, h ♥ червы, d ♦ бубны, c ♣ трефы.
    """)
    if len(variant.deck()) < 52:
        ui.hint("В этой игре короткая колода: карт младше шестёрки нет.")


def show_hand(variant: Variant, cards: Sequence[Card]) -> None:
    """Объясняет, что за комбинация получилась у набора карт."""
    if len(cards) > variant.hole_size + variant.board_size:
        raise ValueError("В «%s» у игрока бывает максимум %d карт."
                         % (variant.name, variant.hole_size + variant.board_size))
    ui.section("Разбор комбинации")
    print("  Карты:      %s" % pretty(cards))
    if variant.board_size and len(cards) > variant.hole_size:
        hole = list(cards[:variant.hole_size])
        board = list(cards[variant.hole_size:])
        print("  Ваши:       %s" % pretty(hole))
        print("  Борд:       %s" % pretty(board))
    else:
        hole, board = list(cards), []
    print("  Комбинация: %s%s%s" % (ui.BOLD, variant.describe(hole, board),
                                    ui.RESET))


def interactive_calculator(variant: Variant) -> None:
    ui.title("%s — калькулятор equity" % variant.name)
    card_help(variant)
    print()
    ui.para("Ваших карт в этой игре: %d.%s" % (
        variant.hole_size,
        "  Общих карт: %d." % variant.board_size if variant.board_size
        else "  Общих карт нет."))

    hero = parse_cards(ui.ask("Ваши карты (%d шт.)" % variant.hole_size))
    board: List[Card] = []
    if variant.board_size:
        board_text = ui.ask("Борд: 3, 4 или 5 карт (Enter — префлоп)")
        if board_text:
            board = parse_cards(board_text)

    villains_text = ui.ask("Карты соперников через / (Enter — неизвестны)")
    players: List[List[Card]] = [hero]
    if villains_text.strip():
        for chunk in villains_text.split("/"):
            players.append(parse_cards(chunk))
    else:
        count_text = ui.ask("Сколько соперников", "1")
        count = int(count_text) if count_text.isdigit() else 1
        players.extend([[] for _ in range(max(1, min(9, count)))])

    pot = bet = None
    pot_text = ui.ask("Размер банка (Enter — пропустить)")
    if pot_text:
        bet_text = ui.ask("Ставка соперника, которую нужно уравнять")
        try:
            pot = float(pot_text.replace(",", "."))
            bet = float(bet_text.replace(",", "."))
        except ValueError:
            ui.bad("Банк и ставка должны быть числами — пропускаю этот блок.")
            pot = bet = None

    analyze(variant, players, board, pot, bet)


def interactive_hand(variant: Variant) -> None:
    ui.title("%s — разбор комбинации" % variant.name)
    card_help(variant)
    print()
    if variant.board_size:
        ui.para("""
            Введите сначала свои карты, потом карты борда — одной строкой.
            Программа разберёт, что получилось.
        """)
    cards = parse_cards(ui.ask("Карты"))
    show_hand(variant, cards)


def terms_for(variant: Variant) -> None:
    ui.title("%s — важные термины" % variant.name)
    ui.para("""
        Здесь только то, что нужно именно для этой игры. Полный словарь:
        python3 poker.py terms
    """)
    for key in variant.terms:
        term = glossary.TERMS.get(key)
        if term:
            glossary.print_term(term)


def build_menu(variant: Variant, lessons_module,
               extras: Sequence[Extra]) -> List[Extra]:
    items: List[Extra] = [
        Extra("lessons", "Уроки — начните отсюда", lambda: None),
        Extra("calc", "Калькулятор equity",
              lambda: interactive_calculator(variant)),
        Extra("showdown", "Квиз: кто выиграл банк",
              lambda: drills.quiz_showdown(variant)),
    ]
    if variant.category_names:
        items.append(Extra("combos", "Квиз: назови комбинацию",
                           lambda: drills.quiz_combinations(variant)))
    if variant.supports_next_card_drill:
        items.append(Extra("drill", "Тренажёр: колл или фолд",
                           lambda: drills.drill_decision(variant)))
    items.extend(extras)
    items.append(Extra("hand", "Разбор комбинации по картам",
                       lambda: interactive_hand(variant)))
    items.append(Extra("terms", "Термины этой игры",
                       lambda: terms_for(variant)))
    return items


def lessons_menu(variant: Variant, lessons_module) -> None:
    while True:
        ui.title("%s — уроки" % variant.name)
        for index, (name, _action) in enumerate(lessons_module.LESSONS, start=1):
            print("  %d. %s" % (index, name))
        print("  a. Пройти все подряд")
        print("  0. Назад")
        choice = ui.ask("Выбор")
        if choice in ("0", ""):
            return
        if choice.lower() == "a":
            for _name, action in lessons_module.LESSONS:
                action()
                ui.pause()
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(lessons_module.LESSONS):
            lessons_module.LESSONS[int(choice) - 1][1]()
            ui.pause()
        else:
            ui.bad("Нет такого пункта.")


def main_menu(variant: Variant, lessons_module,
              extras: Sequence[Extra]) -> None:
    items = build_menu(variant, lessons_module, extras)
    ui.title(variant.name)
    ui.para(variant.short_description.capitalize() + ".")
    while True:
        ui.section("Меню")
        for index, item in enumerate(items, start=1):
            print("  %d. %s" % (index, item.title))
        print("  0. Выход")
        choice = ui.ask("Выбор")
        if choice in ("0", ""):
            print()
            return
        if not choice.isdigit() or not 1 <= int(choice) <= len(items):
            ui.bad("Нет такого пункта.")
            continue
        item = items[int(choice) - 1]
        try:
            if item.key == "lessons":
                lessons_menu(variant, lessons_module)
                continue
            item.action()
        except (BadCard, ValueError) as error:
            ui.bad(str(error))
        ui.pause("Enter — вернуться в меню")


def build_parser(variant: Variant, extras: Sequence[Extra]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="%s/equity_calculator.py" % variant.key,
        description="%s: калькулятор equity и тренажёр (обучающий)." % variant.name,
        epilog="Без аргументов открывается меню.",
    )
    subparsers = parser.add_subparsers(dest="command")

    equity_parser = subparsers.add_parser("equity", help="посчитать equity")
    equity_parser.add_argument("hero", help="ваши карты (%d шт.)" % variant.hole_size)
    if variant.board_size:
        equity_parser.add_argument("--board", default="", help="общие карты")
    equity_parser.add_argument("--vs", default="", dest="versus",
                               help="карты соперников через /")
    equity_parser.add_argument("--opponents", type=int, default=1,
                               help="число соперников с неизвестными картами")
    equity_parser.add_argument("--pot", type=float, help="размер банка")
    equity_parser.add_argument("--bet", type=float,
                               help="ставка, которую нужно уравнять")
    equity_parser.add_argument("--iterations", type=int, default=None,
                               help="число раздач Монте-Карло")

    hand_parser = subparsers.add_parser("hand", help="назвать комбинацию")
    hand_parser.add_argument("cards", help="карты одной строкой")

    lesson_parser = subparsers.add_parser("lesson", help="открыть урок")
    lesson_parser.add_argument("number", nargs="?", help="номер урока или all")

    quiz_parser = subparsers.add_parser("quiz", help="квиз")
    choices = ["showdown"] + (["combos"] if variant.category_names else [])
    quiz_parser.add_argument("kind", nargs="?", default="showdown",
                             choices=choices)
    quiz_parser.add_argument("--rounds", type=int, default=8)

    drill_parser = subparsers.add_parser("drill", help="тренажёр «колл или фолд»")
    drill_parser.add_argument("--rounds", type=int, default=5)

    subparsers.add_parser("terms", help="термины этой игры")
    for extra in extras:
        subparsers.add_parser(extra.key, help=extra.title.lower())
    return parser


def run(variant: Variant, lessons_module, argv: Optional[Sequence[str]] = None,
        extras: Sequence[Extra] = ()) -> int:
    parser = build_parser(variant, extras)
    args = parser.parse_args(argv)
    try:
        return _dispatch(variant, lessons_module, extras, args)
    except (BadCard, ValueError) as error:
        ui.bad(str(error))
        return 1
    except KeyboardInterrupt:
        print()
        return 130


def _dispatch(variant: Variant, lessons_module, extras: Sequence[Extra],
              args: argparse.Namespace) -> int:
    if args.command == "equity":
        hero = parse_cards(args.hero)
        board = parse_cards(getattr(args, "board", "") or "")
        players: List[List[Card]] = [hero]
        if args.versus:
            players.extend(parse_cards(chunk) for chunk in args.versus.split("/"))
        else:
            players.extend([[] for _ in range(max(1, args.opponents))])
        analyze(variant, players, board, args.pot, args.bet, args.iterations)
        return 0

    if args.command == "hand":
        show_hand(variant, parse_cards(args.cards))
        return 0

    if args.command == "lesson":
        lessons = lessons_module.LESSONS
        if not args.number:
            ui.title("%s — уроки" % variant.name)
            for index, (name, _action) in enumerate(lessons, start=1):
                print("  %d. %s" % (index, name))
            return 0
        if args.number == "all":
            for _name, action in lessons:
                action()
            return 0
        if args.number.isdigit() and 1 <= int(args.number) <= len(lessons):
            lessons[int(args.number) - 1][1]()
            return 0
        ui.bad("Урока с номером %s нет." % args.number)
        return 1

    if args.command == "quiz":
        if args.kind == "combos":
            drills.quiz_combinations(variant, args.rounds)
        else:
            drills.quiz_showdown(variant, args.rounds)
        return 0

    if args.command == "drill":
        drills.drill_decision(variant, args.rounds)
        return 0

    if args.command == "terms":
        terms_for(variant)
        return 0

    for extra in extras:
        if args.command == extra.key:
            extra.action()
            return 0

    main_menu(variant, lessons_module, extras)
    return 0
