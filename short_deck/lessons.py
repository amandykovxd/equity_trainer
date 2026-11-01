"""Уроки шортдек-холдема.

Предполагается, что правила обычного холдема вы уже знаете — если нет,
сначала пройдите уроки в папке texas_holdem.
"""
from __future__ import annotations

from typing import Callable, List, Tuple

from core import ui
from core.cards import parse_cards, pretty, short_deck
from core.equity import equity
from short_deck.rules import SD_CATEGORY_NAMES, SD_ORDER, VARIANT, describe


def lesson_rules() -> None:
    ui.title("Урок 1. Короткая колода и новый порядок комбинаций")
    ui.para("""
        Шортдек — это холдем, из колоды которого убрали все карты
        младше шестёрки. Остаётся 36 карт вместо 52: шестёрки,
        семёрки, восьмёрки, девятки, десятки, валеты, дамы, короли
        и тузы.

        Раздача идёт точно так же: 2 своих карты, 5 общих, четыре круга
        ставок. Но порядок старшинства комбинаций меняется — и это
        не прихоть, а следствие арифметики.
    """)

    ui.section("Что поменялось")
    ui.block("""
        Флеш теперь СИЛЬНЕЕ фулл-хауса.
        Тройка теперь СИЛЬНЕЕ стрита.
    """)
    print()
    ui.para("""
        Причина в том, что в короткой колоде каждой масти всего 9 карт
        вместо 13, поэтому флеш собрать стало труднее, чем фулл-хаус.
        А стрит, наоборот, собирается легче: карты идут плотнее, и любые
        пять подряд оказываются ближе друг к другу.

        В покере комбинации всегда расставлены по редкости: чем реже
        комбинация, тем она сильнее. Колода изменилась — изменился
        и порядок.
    """)

    ui.section("Полный порядок от сильнейшей к слабейшей")
    print()
    for index, category in enumerate(SD_ORDER, start=1):
        mark = ""
        if SD_CATEGORY_NAMES[category] in ("Флеш", "Тройка"):
            mark = ui.color("   ← поднялась", ui.YELLOW)
        print("  %2d. %s%s" % (index, SD_CATEGORY_NAMES[category], mark))

    ui.section("Ещё одно отличие: младший стрит")
    hand = parse_cards("As6d7h8c9s")
    print("  %s  →  %s" % (pretty(hand), describe(hand)))
    print()
    ui.para("""
        Двоек, троек, четвёрок и пятёрок в колоде нет, поэтому туз
        работает как пятёрка: A-6-7-8-9 — это самый младший стрит
        шортдека. Старший стрит, как обычно, 10-J-Q-K-A.
    """)


def lesson_probabilities() -> None:
    ui.title("Урок 2. Почему порядок именно такой")
    ui.para("""
        Не верьте на слово — проверим. Раздадим много случайных рук
        по 7 карт из обеих колод и посчитаем, как часто встречается
        каждая комбинация.
    """)
    import random

    from core.cards import full_deck
    from core.evaluator import CATEGORY_NAMES_RU, CATEGORY_ORDER
    from core.evaluator import evaluate as evaluate_full
    from short_deck.rules import evaluate as evaluate_short

    rounds = 40_000
    rng = random.Random(1)
    counts_full = {category: 0 for category in CATEGORY_ORDER}
    counts_short = {category: 0 for category in SD_ORDER}

    deck_full, deck_short = full_deck(), short_deck()
    for _ in range(rounds):
        counts_full[evaluate_full(rng.sample(deck_full, 7))[0]] += 1
        counts_short[evaluate_short(rng.sample(deck_short, 7))[0]] += 1

    ui.section("Частота комбинаций на %d случайных раздачах" % rounds)
    print()
    print("  %-16s %12s %12s" % ("комбинация", "52 карты", "36 карт"))
    print("  " + "-" * 42)
    pairs = [
        ("Флеш", 5, 6),
        ("Фулл-хаус", 6, 5),
        ("Тройка", 3, 4),
        ("Стрит", 4, 3),
    ]
    for name, full_key, short_key in pairs:
        print("  %-16s %11.2f%% %11.2f%%"
              % (name, counts_full[full_key] / rounds * 100,
                 counts_short[short_key] / rounds * 100))
    print()
    ui.para("""
        Видно главное: в короткой колоде флеш встречается реже
        фулл-хауса, а тройка — реже стрита. Поэтому их и поменяли
        местами. Числа посчитаны прямо сейчас, а не взяты из книги.
    """)
    ui.hint("Если забудете порядок — вспомните логику: чем реже "
            "комбинация в этой колоде, тем она сильнее.")


def lesson_play() -> None:
    ui.title("Урок 3. Как меняется сама игра")
    ui.para("""
        Короткая колода делает руки ближе друг к другу по силе.
        Это главное практическое следствие.
    """)

    ui.section("Сравним те же руки в двух играх")
    from texas_holdem.rules import VARIANT as HOLDEM

    cases = [
        ("AsAh", "KsKd", "Тузы против королей"),
        ("AsKs", "QhQd", "Туз-король одномастные / дамы"),
        ("AsAh", None, "Тузы против случайной руки"),
    ]
    print()
    print("  %-26s %10s %10s" % ("", "52 карты", "36 карт"))
    for hero_text, villain_text, comment in cases:
        hero = parse_cards(hero_text)
        if villain_text:
            villain = parse_cards(villain_text)
            full = equity(HOLDEM, [hero, villain], seed=4)
            short = equity(VARIANT, [hero, villain], seed=4)
        else:
            full = equity(HOLDEM, [hero, []], seed=4)
            short = equity(VARIANT, [hero, []], seed=4)
        print("  %-26s %9.1f%% %9.1f%%"
              % (comment, full.hero_equity * 100, short.hero_equity * 100))
    print()
    ui.para("""
        Разрыв сокращается: в короткой колоде у соперника больше шансов
        попасть во что-то полезное. Поэтому в шортдеке играют агрессивнее
        и заходят в банки чаще — преимущество одной руки над другой
        меньше, и ждать идеальных карт бессмысленно.
    """)

    ui.section("На что обращать внимание новичку")
    ui.para("""
        1. Пара без поддержки стоит мало: стриты и тройки собираются
           часто, и ваша пара быстро оказывается второй.

        2. Флеш-дро стало дороже: флеш теперь сильнее фулл-хауса,
           но собрать его труднее — аутов всего 8, а не 9, потому что
           в масти 9 карт вместо 13.

        3. Стриты повсюду. Карты идут плотно, и связанные руки
           вроде 9-8 набирают ценность.
    """)
    ui.hint("Шортдек часто играют с анте от всех игроков вместо "
            "блайндов. Это ещё одна причина играть активнее: "
            "в банке с самого начала есть за что бороться.")


LESSONS: List[Tuple[str, Callable[[], None]]] = [
    ("Короткая колода и новый порядок комбинаций", lesson_rules),
    ("Почему порядок именно такой (считаем частоты)", lesson_probabilities),
    ("Как меняется сама игра", lesson_play),
]
