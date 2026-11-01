"""Уроки омахи хай-лоу (Omaha/8).

Предполагается, что правила омахи вы уже знаете — если нет, сначала
пройдите уроки в папке omaha.
"""
from __future__ import annotations

from typing import Callable, List, Tuple

from core import ui
from core.cards import parse_cards, pretty
from core.equity import equity
from omaha_hi_lo.rules import VARIANT


def lesson_rules() -> None:
    ui.title("Урок 1. Делёж банка: хай и лоу")
    ui.para("""
        Раздача идёт точно как в обычной омахе: 4 своих карты, 5 общих,
        комбинация из ровно двух своих и ровно трёх общих. Отличие
        в том, кто забирает банк.
    """)
    ui.section("Две половины банка")
    ui.block("""
        Хай — половина банка уходит сильнейшей комбинации (как обычно).
        Лоу — половина банка уходит слабейшей руке по системе A-5.
    """)
    print()
    ui.para("""
        Но лоу существует не всегда. Чтобы лоу считалось собранным,
        нужны пять РАЗНЫХ карт достоинством 8 или ниже (туз считается
        за единицу). Это называется квалификацией, или правилом
        «eight or better».

        Если лоу не собралось ни у кого, весь банк забирает хай-рука.
    """)

    ui.section("Пример: лоу есть")
    hero = parse_cards("As2d7h8c")
    board = parse_cards("5h4c9sKd7s")
    print("  Ваши карты: %s" % pretty(hero))
    print("  Борд:       %s" % pretty(board))
    print()
    print("  %s" % VARIANT.describe_high(hero, board))
    print("  %s" % VARIANT.describe_low(hero, board))
    ui.para("""
        Для лоу взяты туз и двойка из руки и 7-5-4 с борда — ровно две
        свои карты и ровно три общие, и все пять разного достоинства,
        не старше восьмёрки.
    """, indent=4)

    ui.section("Пример: лоу нет ни у кого")
    board2 = parse_cards("KdQh9s9cJh")
    print("  Ваши карты: %s" % pretty(hero))
    print("  Борд:       %s" % pretty(board2))
    print()
    print("  %s" % VARIANT.describe_low(hero, board2))
    ui.para("""
        На борде нет трёх разных низких карт, а значит собрать лоу
        физически невозможно — ни вам, ни соперникам. Весь банк уйдёт
        за хай.
    """, indent=4)
    ui.hint("Первое, что нужно посмотреть на флопе: есть ли на борде "
            "хотя бы три разные карты от восьмёрки и ниже. Нет — "
            "играйте обычную омаху.")


def lesson_scoop() -> None:
    ui.title("Урок 2. Скуп — то, ради чего здесь играют")
    ui.para("""
        Забрать обе половины банка называется «скуп». Разница между
        скупом и половиной банка огромна: половина часто лишь
        возвращает вложенное, а скуп — это и есть прибыль.
    """)

    ui.section("Сравним две руки")
    cases = [
        ("As2s3d4c", "Туз-двойка с поддержкой: играет в обе стороны"),
        ("AsAhKdKc", "Тузы с королями — топ-рука обычной омахи, "
                     "но лоу ею не собрать"),
        ("9s9hTcTd", "Средние пары: ни хай, ни лоу"),
    ]
    villain = parse_cards("KsKhQdJc")
    print()
    print("  Против одной и той же руки соперника: %s" % pretty(villain))
    print()
    for hand_text, comment in cases:
        hero = parse_cards(hand_text)
        result = equity(VARIANT, [hero, villain], seed=9)
        print("  %s  equity %5.1f%%   хай %.0f%%  лоу %.0f%%  скуп %.0f%%"
              % (ui.pad(pretty(hero), 20), result.hero_equity * 100,
                 result.hero_high_share * 100, result.hero_low_share * 100,
                 result.hero_scoops * 100))
        ui.para(comment, indent=6)
    print()
    ui.para("""
        Обратите внимание на руку с тузом и двойкой: по хаю она слабее
        тузов с королями, но лоу-половину забирает очень часто, и общая
        equity выходит сопоставимой.
    """)
    ui.hint("Главный признак хорошей руки в хай-лоу — умение играть "
            "в обе стороны. Туз с двойкой плюс две связанные старшие "
            "карты — это и есть идеал.")


def lesson_counterfeit() -> None:
    ui.title("Урок 3. Каунтерфейт: как лоу теряет ценность")
    ui.para("""
        Собранное лоу — не навсегда. Карта на борде может сделать вашу
        руку бесполезной, даже не изменив её. Это самая частая
        неприятность в хай-лоу, и называется она каунтерфейт.
    """)

    hero = parse_cards("As2d9hTc")
    villain = parse_cards("Ad5c9sTd")
    flop = parse_cards("3h4c7s")

    ui.section("На флопе у вас лучшее лоу")
    print("  Ваши карты:      %s" % pretty(hero))
    print("  Карты соперника: %s" % pretty(villain))
    print("  Борд:            %s" % pretty(flop))
    print()
    print("  У вас:      %s" % VARIANT.describe_low(hero, flop))
    print("  У соперника: %s" % VARIANT.describe_low(villain, flop))
    ui.para("""
        Сравнивают лоу по старшим картам: у обоих семёрка, дальше у вас
        четвёрка, у соперника пятёрка. Четвёрка младше — значит лоу
        лучше у вас.
    """, indent=4)

    turn = parse_cards("3h4c7s2c")
    ui.section("На тёрне выходит двойка — и всё меняется")
    print("  Борд:       %s" % pretty(turn))
    print()
    print("  У вас:      %s" % VARIANT.describe_low(hero, turn))
    print("  У соперника: %s" % VARIANT.describe_low(villain, turn))
    ui.para("""
        Ваше лоу не изменилось вообще. Но двойка теперь лежит на борде,
        то есть доступна всем — и ваша двойка перестала быть ценной.
        Соперник берёт двойку с борда вместе со своей пятёркой
        и собирает колесо, которое вас обходит.
    """, indent=4)
    ui.hint("Каунтерфейт — это не ухудшение вашей руки, а обесценивание "
            "того, что делало её сильной.")

    ui.section("Как от этого страхуются")
    ui.para("""
        Рука A-2-3 защищена: если двойка на борде обесценит двойку,
        останется тройка. Поэтому третья низкая карта в руке стоит
        дороже, чем кажется, а «голые» A-2 без поддержки — рука
        заметно более хрупкая, чем выглядит.
    """)


LESSONS: List[Tuple[str, Callable[[], None]]] = [
    ("Делёж банка: хай и лоу", lesson_rules),
    ("Скуп — то, ради чего здесь играют", lesson_scoop),
    ("Каунтерфейт: как лоу теряет ценность", lesson_counterfeit),
]
