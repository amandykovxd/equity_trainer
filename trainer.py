#!/usr/bin/env python3
"""Покерный тренажёр и калькулятор equity для техасского холдема.

Запуск без аргументов — интерактивное меню (с него и начинайте):

    python3 trainer.py

Можно вызывать и напрямую:

    python3 trainer.py lesson 2                  # урок про комбинации
    python3 trainer.py hand AhKhQhJhTh           # что это за комбинация
    python3 trainer.py equity AhKh --board Kh7h2c --vs KsQd --pot 100 --bet 50
    python3 trainer.py equity AsAh --opponents 5 # против 5 случайных рук
    python3 trainer.py chart                     # таблица стартовых рук
    python3 trainer.py quiz combos               # квиз на комбинации
    python3 trainer.py drill                     # тренажёр «колл или фолд»
    python3 trainer.py test                      # самопроверка расчётов

Этот скрипт — обучающий. Он не подключается ни к одному покер-руму,
ничего не читает с экрана и не подсказывает в реальном времени:
использование подобных помощников во время игры запрещено правилами
всех легальных румов. Считайте его тренажёром между сессиями.
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from poker import drills, lessons, ranges, ui
from poker.cards import BadCard, Card, check_no_duplicates, parse_cards, pretty
from poker.equity import (
    equity,
    exact_improve_chance,
    improving_cards,
    outs_vs_villain,
    required_equity,
    rule_of_2_and_4,
)
from poker.evaluator import best_five, describe

ITERATIONS = 25_000


# --------------------------------------------------------------------------
# Разбор рук и расчёт
# --------------------------------------------------------------------------

def show_hand(cards: Sequence[Card]) -> None:
    """Объясняет, что за комбинация у набора карт."""
    if len(cards) < 5:
        ui.bad("Для комбинации нужно минимум 5 карт, передано %d." % len(cards))
        return
    ui.section("Разбор комбинации")
    print("  Карты:      %s" % pretty(cards))
    print("  Комбинация: %s%s%s" % (ui.BOLD, describe(cards), ui.RESET))
    if len(cards) > 5:
        print("  Играют:     %s" % pretty(best_five(cards)))
        unused = [card for card in cards if card not in best_five(cards)]
        print("  Не играют:  %s" % pretty(unused))


def analyze(
    hero: Sequence[Card],
    villains: Sequence[Optional[Sequence[Card]]],
    board: Sequence[Card],
    pot: Optional[float] = None,
    bet: Optional[float] = None,
    iterations: int = ITERATIONS,
) -> None:
    """Полный разбор ситуации: equity, аутсы и решение по пот-оддсам."""
    # Проверяем ввод до того, как что-то посчитаем и напечатаем: иначе
    # пользователь увидит разбор руки, собранной из несуществующей колоды.
    check_no_duplicates(hero, board, *[v for v in villains if v is not None])
    if len(hero) != 2:
        raise ValueError("У вас должно быть ровно 2 карты, передано %d." % len(hero))
    if board and len(board) not in (3, 4, 5):
        raise ValueError("На борде бывает 3, 4 или 5 карт, передано %d." % len(board))

    ui.section("Ситуация")
    print("  Ваши карты: %s" % pretty(hero))
    print("  Борд:       %s" % pretty(board))
    for index, villain in enumerate(villains, start=1):
        if villain is None:
            print("  Соперник %d: карты неизвестны (считаем против любой руки)" % index)
        else:
            print("  Соперник %d: %s" % (index, pretty(villain)))

    if board:
        print()
        print("  Сейчас у вас: %s%s%s"
              % (ui.BOLD, describe(list(hero) + list(board)), ui.RESET))
        known_villains = [v for v in villains if v is not None]
        if len(known_villains) == 1:
            print("  У соперника:  %s"
                  % describe(list(known_villains[0]) + list(board)))

    result = equity(hero, villains, board, iterations=iterations)
    ui.section("Equity")
    print("  %s  %.1f%%" % (ui.bar(result.hero_equity, 30), result.hero_equity * 100))
    print()
    print(result.summary())

    # Аутсы имеют смысл только на флопе/тёрне и против известной руки.
    known = [v for v in villains if v is not None]
    if 3 <= len(board) <= 4 and len(known) == 1 and len(villains) == 1:
        outs, ties = outs_vs_villain(hero, known[0], board)
        cards_to_come = 5 - len(board)
        unseen = 52 - 2 - len(board) - 2
        ui.section("Аутсы")
        if outs:
            print("  Аутсов: %d — %s"
                  % (len(outs), pretty(sorted(outs, key=lambda c: (-c.rank, c.suit)))))
            print("  Правило %d: %d × %d = %.0f%%"
                  % (2 if cards_to_come == 1 else 4, len(outs),
                     2 if cards_to_come == 1 else 4,
                     rule_of_2_and_4(len(outs), cards_to_come) * 100))
            print("  Точно:      %.1f%% (попасть хотя бы раз за %d карт%s)"
                  % (exact_improve_chance(len(outs), unseen, cards_to_come) * 100,
                     cards_to_come, "у" if cards_to_come == 1 else "ы"))
        else:
            print("  Аутсов нет: ни одна карта не выводит вас вперёд.")
        if ties:
            print("  Ничья при: %s" % pretty(ties))
    elif 3 <= len(board) <= 4 and not known:
        better = improving_cards(hero, board)
        ui.section("Карты, усиливающие вашу комбинацию")
        print("  Таких карт %d: %s"
              % (len(better), pretty(sorted(better, key=lambda c: (-c.rank, c.suit)))))
        ui.hint("Карты соперника неизвестны, поэтому это не аутсы в строгом "
                "смысле — просто карты, которые делают вашу руку сильнее.")

    if pot is not None and bet:
        need = required_equity(pot, bet)
        expected_value = result.hero_equity * (pot + bet) - bet
        ui.section("Решение по пот-оддсам")
        print("  В банке %.0f, ставка соперника %.0f." % (pot, bet))
        print("  Требуемая equity: %.1f%%   (%.0f / %.0f)"
              % (need * 100, bet, pot + bet))
        print("  Ваша equity:      %.1f%%" % (result.hero_equity * 100))
        print("  Ожидание колла:   %+.1f" % expected_value)
        print()
        if result.hero_equity > need:
            ui.good("Колл выгоден (+%.1f п.п. equity сверх требуемой)."
                    % ((result.hero_equity - need) * 100))
        else:
            ui.bad("Колл убыточен (не хватает %.1f п.п. equity) — фолд."
                   % ((need - result.hero_equity) * 100))
        ui.hint("Это расчёт только для колла. Рейз может быть выгоден и там, "
                "где колл убыточен — но это следующая ступень обучения.")

    if not board:
        notation, tier, advice = ranges.advice_for(hero)
        ui.section("Стартовая рука")
        print("  Обозначение: %s     Группа: %s%s%s"
              % (notation, ui.BOLD, ranges.TIER_NAMES[tier], ui.RESET))
        ui.para("  " + advice)


# --------------------------------------------------------------------------
# Интерактивный калькулятор
# --------------------------------------------------------------------------

def interactive_calculator() -> None:
    ui.title("Калькулятор equity")
    ui.para("""
        Карты вводятся как номинал + масть: As = туз пик, Th или 10h =
        десятка червей, 7d = семёрка бубен.
        Масти: s ♠ пики, h ♥ червы, d ♦ бубны, c ♣ трефы.
    """)
    try:
        hero = parse_cards(ui.ask("Ваши 2 карты (например AhKh)"))
        if len(hero) != 2:
            ui.bad("Нужно ровно 2 карты.")
            return

        board_text = ui.ask("Борд: 3, 4 или 5 карт (Enter — префлоп)")
        board = parse_cards(board_text) if board_text else []
        if board and len(board) not in (3, 4, 5):
            ui.bad("На борде бывает 3, 4 или 5 карт.")
            return

        villains_text = ui.ask(
            "Карты соперников через / (Enter — неизвестны)")
        villains: List[Optional[List[Card]]] = []
        if villains_text.strip():
            for chunk in villains_text.split("/"):
                hand = parse_cards(chunk)
                if len(hand) != 2:
                    ui.bad("У каждого соперника должно быть 2 карты.")
                    return
                villains.append(hand)
        else:
            count_text = ui.ask("Сколько соперников", "1")
            count = int(count_text) if count_text.isdigit() else 1
            villains = [None] * max(1, min(9, count))

        pot = bet = None
        pot_text = ui.ask("Размер банка (Enter — пропустить)")
        if pot_text:
            bet_text = ui.ask("Ставка соперника, которую нужно уравнять")
            try:
                pot, bet = float(pot_text.replace(",", ".")), float(bet_text.replace(",", "."))
            except ValueError:
                ui.bad("Банк и ставка должны быть числами — пропускаю этот блок.")
                pot = bet = None

        analyze(hero, villains, board, pot, bet)
    except BadCard as error:
        ui.bad(str(error))
    except ValueError as error:
        ui.bad(str(error))


def interactive_hand() -> None:
    ui.title("Разбор комбинации")
    ui.para("""
        Введите от 5 до 7 карт — скрипт назовёт комбинацию и покажет,
        какие именно пять карт в неё входят.
    """)
    try:
        cards = parse_cards(ui.ask("Карты (например AsKdQh9c4s)"))
    except BadCard as error:
        ui.bad(str(error))
        return
    show_hand(cards)


# --------------------------------------------------------------------------
# Меню
# --------------------------------------------------------------------------

MENU = [
    ("Уроки — начните отсюда", None),
    ("Калькулятор equity", interactive_calculator),
    ("Квиз: назови комбинацию", lambda: drills.quiz_combinations()),
    ("Квиз: кто выиграл банк", lambda: drills.quiz_showdown()),
    ("Квиз: посчитай аутсы", lambda: drills.quiz_outs()),
    ("Квиз: стартовые руки", lambda: drills.quiz_preflop()),
    ("Тренажёр: колл или фолд", lambda: drills.drill_decision()),
    ("Таблица стартовых рук", lessons.print_chart),
    ("Разбор комбинации по картам", interactive_hand),
]


def lessons_menu() -> None:
    while True:
        ui.title("Уроки")
        for index, (name, _function) in enumerate(lessons.LESSONS, start=1):
            print("  %d. %s" % (index, name))
        print("  a. Пройти все подряд")
        print("  0. Назад")
        choice = ui.ask("Выбор")
        if choice in ("0", ""):
            return
        if choice.lower() == "a":
            for _name, function in lessons.LESSONS:
                function()
                ui.pause()
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(lessons.LESSONS):
            lessons.LESSONS[int(choice) - 1][1]()
            ui.pause()
        else:
            ui.bad("Нет такого пункта.")


def main_menu() -> None:
    ui.title("Покерный тренажёр: от нуля до расчёта equity")
    ui.para("""
        Если вы совсем новичок — пройдите уроки 1 и 2, потом возьмите
        квиз на комбинации. Остальное имеет смысл только после этого.
    """)
    while True:
        ui.section("Главное меню")
        for index, (name, _function) in enumerate(MENU, start=1):
            print("  %d. %s" % (index, name))
        print("  0. Выход")
        choice = ui.ask("Выбор")
        if choice in ("0", ""):
            print("\n  Удачи за столом. Играйте только на условные деньги, "
                  "пока не станет скучно.\n")
            return
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            ui.bad("Нет такого пункта.")
            continue
        index = int(choice) - 1
        if index == 0:
            lessons_menu()
            continue
        try:
            MENU[index][1]()
        except (BadCard, ValueError) as error:
            ui.bad(str(error))
        ui.pause("Enter — вернуться в меню")


# --------------------------------------------------------------------------
# Командная строка
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Покерный тренажёр и калькулятор equity (обучающий).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Без аргументов открывается интерактивное меню.",
    )
    subparsers = parser.add_subparsers(dest="command")

    equity_parser = subparsers.add_parser("equity", help="посчитать equity")
    equity_parser.add_argument("hero", help="ваши 2 карты, например AhKh")
    equity_parser.add_argument("--board", default="", help="борд, например Kh7h2c")
    equity_parser.add_argument("--vs", default="", dest="versus",
                               help="карты соперников через /, например KsQd/7h7d")
    equity_parser.add_argument("--opponents", type=int, default=1,
                               help="число соперников с неизвестными картами")
    equity_parser.add_argument("--pot", type=float, help="размер банка")
    equity_parser.add_argument("--bet", type=float, help="ставка, которую нужно уравнять")
    equity_parser.add_argument("--iterations", type=int, default=ITERATIONS,
                               help="число раздач Монте-Карло")

    hand_parser = subparsers.add_parser("hand", help="назвать комбинацию")
    hand_parser.add_argument("cards", help="от 5 до 7 карт")

    lesson_parser = subparsers.add_parser("lesson", help="открыть урок")
    lesson_parser.add_argument("number", nargs="?", help="номер урока или all")

    quiz_parser = subparsers.add_parser("quiz", help="квиз")
    quiz_parser.add_argument("kind", nargs="?", default="combos",
                             choices=["combos", "showdown", "outs", "preflop"])
    quiz_parser.add_argument("--rounds", type=int, default=8)

    drill_parser = subparsers.add_parser("drill", help="тренажёр «колл или фолд»")
    drill_parser.add_argument("--rounds", type=int, default=5)

    subparsers.add_parser("chart", help="таблица стартовых рук")
    subparsers.add_parser("test", help="самопроверка расчётов")
    return parser


def run_command(args: argparse.Namespace) -> int:
    if args.command == "equity":
        hero = parse_cards(args.hero)
        board = parse_cards(args.board) if args.board else []
        if args.versus:
            villains: List[Optional[List[Card]]] = [
                parse_cards(chunk) for chunk in args.versus.split("/")
            ]
        else:
            villains = [None] * max(1, args.opponents)
        analyze(hero, villains, board, args.pot, args.bet, args.iterations)
        return 0

    if args.command == "hand":
        show_hand(parse_cards(args.cards))
        return 0

    if args.command == "lesson":
        if not args.number:
            ui.title("Уроки")
            for index, (name, _function) in enumerate(lessons.LESSONS, start=1):
                print("  %d. %s" % (index, name))
            return 0
        if args.number == "all":
            for _name, function in lessons.LESSONS:
                function()
            return 0
        if args.number.isdigit() and 1 <= int(args.number) <= len(lessons.LESSONS):
            lessons.LESSONS[int(args.number) - 1][1]()
            return 0
        ui.bad("Урока с номером %s нет." % args.number)
        return 1

    if args.command == "quiz":
        {
            "combos": drills.quiz_combinations,
            "showdown": drills.quiz_showdown,
            "outs": drills.quiz_outs,
            "preflop": drills.quiz_preflop,
        }[args.kind](args.rounds)
        return 0

    if args.command == "drill":
        drills.drill_decision(args.rounds)
        return 0

    if args.command == "chart":
        lessons.print_chart()
        return 0

    if args.command == "test":
        import selftest
        return selftest.run()

    main_menu()
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_command(args)
    except BadCard as error:
        ui.bad(str(error))
        return 1
    except ValueError as error:
        ui.bad(str(error))
        return 1
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
