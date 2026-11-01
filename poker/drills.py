"""Тренажёры: квизы на комбинации, аутсы и практика решений.

Вся теория бесполезна, пока решения не доведены до автоматизма.
Здесь скрипт раздаёт случайные ситуации, спрашивает вас, а потом
показывает расчёт — чтобы вы видели не только «верно/неверно»,
но и откуда берётся правильный ответ.
"""
from __future__ import annotations

import random
from typing import List, Optional, Sequence, Tuple

from . import ranges, ui
from .cards import Card, full_deck, pretty
from .equity import equity, outs_vs_villain, required_equity
from .evaluator import (
    CATEGORY_NAMES_RU,
    best_five,
    FLUSH,
    FOUR_OF_A_KIND,
    FULL_HOUSE,
    HIGH_CARD,
    ONE_PAIR,
    STRAIGHT,
    STRAIGHT_FLUSH,
    THREE_OF_A_KIND,
    TWO_PAIR,
    category_of,
    describe,
    evaluate,
)

CATEGORY_ORDER = [
    STRAIGHT_FLUSH, FOUR_OF_A_KIND, FULL_HOUSE, FLUSH, STRAIGHT,
    THREE_OF_A_KIND, TWO_PAIR, ONE_PAIR, HIGH_CARD,
]


# --------------------------------------------------------------------------
# Раздача ситуаций
# --------------------------------------------------------------------------

def _ranks_of(cards: Sequence[Card]) -> List[int]:
    return [card.rank for card in cards]


def _straight_ranks(high: int) -> List[int]:
    """Пять номиналов стрита. В «колесе» (A-2-3-4-5) туз работает как единица."""
    return [14 if rank == 1 else rank for rank in range(high, high - 5, -1)]


def _recipe(target: int, rng: random.Random) -> List[Card]:
    """Собирает 7 карт, которые скорее всего дадут нужную комбинацию."""
    deck = full_deck()
    rng.shuffle(deck)
    by_rank = {}
    for card in deck:
        by_rank.setdefault(card.rank, []).append(card)

    chosen: List[Card] = []
    if target == STRAIGHT_FLUSH:
        suit = rng.choice("shdc")
        chosen = [Card(rank, suit) for rank in _straight_ranks(rng.randint(5, 14))]
    elif target == FOUR_OF_A_KIND:
        rank = rng.randint(2, 14)
        chosen = list(by_rank[rank])
    elif target == FULL_HOUSE:
        trips, pair = rng.sample(range(2, 15), 2)
        chosen = by_rank[trips][:3] + by_rank[pair][:2]
    elif target == FLUSH:
        suit = rng.choice("shdc")
        suited = [card for card in deck if card.suit == suit]
        chosen = rng.sample(suited, 5)
    elif target == STRAIGHT:
        chosen = [rng.choice(by_rank[rank])
                  for rank in _straight_ranks(rng.randint(5, 14))]
    elif target == THREE_OF_A_KIND:
        rank = rng.randint(2, 14)
        chosen = by_rank[rank][:3]
    elif target == TWO_PAIR:
        first, second = rng.sample(range(2, 15), 2)
        chosen = by_rank[first][:2] + by_rank[second][:2]
    elif target == ONE_PAIR:
        rank = rng.randint(2, 14)
        chosen = by_rank[rank][:2]

    rest = [card for card in deck if card not in set(chosen)]
    return chosen + rest[: 7 - len(chosen)]


def deal_with_category(target: int, rng: random.Random) -> List[Card]:
    """Семь карт с заданной комбинацией.

    Случайные карты-добивки иногда усиливают руку сильнее задуманного
    (например, пара превращается в две пары), поэтому собираем заново,
    пока не получится ровно нужная категория.
    """
    for _ in range(4000):
        cards = _recipe(target, rng)
        if category_of(cards) == target:
            return cards
    # Теоретически недостижимо, но пусть функция всегда что-то возвращает.
    return _recipe(target, rng)


def deal_draw_spot(rng: random.Random) -> Tuple[List[Card], List[Card], List[Card]]:
    """Ситуация на флопе, где герой проигрывает, но имеет аутсы."""
    while True:
        deck = full_deck()
        rng.shuffle(deck)
        hero, villain, board = deck[:2], deck[2:4], deck[4:7]
        hero_score = evaluate(hero + board)
        villain_score = evaluate(villain + board)
        if hero_score >= villain_score:
            continue
        outs, _ties = outs_vs_villain(hero, villain, board)
        if 2 <= len(outs) <= 15:
            return hero, villain, board


# --------------------------------------------------------------------------
# Квизы
# --------------------------------------------------------------------------

def quiz_combinations(rounds: int = 8, rng: Optional[random.Random] = None) -> None:
    """«Что у меня собралось?» — узнавание комбинации из 7 карт."""
    rng = rng or random.Random()
    ui.title("Квиз: назови комбинацию")
    ui.para("""
        Вам показывают 2 ваши карты и 5 общих. Нужно понять, какая
        комбинация получилась. Помните: считаются лучшие 5 карт из 7.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        target = rng.choice(CATEGORY_ORDER)
        cards = deal_with_category(target, rng)
        hero, board = cards[:2], cards[2:]

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Ваши карты: %s" % pretty(hero))
        print("  Борд:       %s" % pretty(board))
        print()
        for index, category in enumerate(CATEGORY_ORDER, start=1):
            print("    %d) %s" % (index, CATEGORY_NAMES_RU[category]))
        print()
        answer = ui.ask("Номер ответа")
        if not answer.isdigit() or not 1 <= int(answer) <= len(CATEGORY_ORDER):
            ui.bad("Нужен номер от 1 до %d — считаю как неверный ответ."
                   % len(CATEGORY_ORDER))
            chosen = None
        else:
            chosen = CATEGORY_ORDER[int(answer) - 1]

        actual = category_of(cards)
        if chosen == actual:
            correct += 1
            ui.good("Верно: %s" % describe(cards))
        else:
            ui.bad("Правильный ответ: %s" % describe(cards))
        print("     Комбинацию составляют: %s" % pretty(best_five(cards)))

    _report(correct, rounds)


def quiz_showdown(rounds: int = 8, rng: Optional[random.Random] = None) -> None:
    """«Кто выиграл?» — сравнение двух рук на вскрытии."""
    rng = rng or random.Random()
    ui.title("Квиз: кто выиграл банк")
    ui.para("""
        Вскрытие: видны карты обоих игроков и все 5 общих карт.
        Определите победителя. Этот квиз быстрее всего учит замечать
        кикеры и «общие» комбинации на борде.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        deck = full_deck()
        rng.shuffle(deck)
        hero, villain, board = deck[:2], deck[2:4], deck[4:9]

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Борд:      %s" % pretty(board))
        print("  Игрок 1:   %s" % pretty(hero))
        print("  Игрок 2:   %s" % pretty(villain))
        print()
        answer = ui.ask_choice("Кто выигрывает? 1 — первый, 2 — второй, s — сплит",
                              "12s")

        hero_score = evaluate(hero + board)
        villain_score = evaluate(villain + board)
        if hero_score > villain_score:
            truth = "1"
        elif villain_score > hero_score:
            truth = "2"
        else:
            truth = "s"

        if answer == truth:
            correct += 1
            ui.good("Верно.")
        else:
            ui.bad("Неверно.")
        print("     Игрок 1: %s" % describe(hero + board))
        print("     Игрок 2: %s" % describe(villain + board))
        if truth == "s":
            print("     Банк делится пополам.")

    _report(correct, rounds)


def quiz_outs(rounds: int = 5, rng: Optional[random.Random] = None) -> None:
    """«Сколько у меня аутсов?» — счёт аутсов на флопе."""
    rng = rng or random.Random()
    ui.title("Квиз: посчитай аутсы")
    ui.para("""
        Во всех ситуациях ниже вы проигрываете прямо сейчас, но карты
        соперника вам открыты. Сколько карт тёрна сделают вашу руку
        сильнее его руки? Ответ в пределах ±1 считается верным:
        за столом важна оценка, а не точность до карты.

        Equity внизу ответа может заметно отличаться от «аутсы × 4»:
        правило считает только попадание в аут, а equity учитывает ещё
        и карты ривера, и то, что иногда рука выигрывает другим способом.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        hero, villain, board = deal_draw_spot(rng)
        outs, ties = outs_vs_villain(hero, villain, board)

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Ваши карты:      %s   (%s)" % (pretty(hero), describe(hero + board)))
        print("  Борд (флоп):     %s" % pretty(board))
        print("  Карты соперника: %s   (%s)"
              % (pretty(villain), describe(villain + board)))
        print()
        answer = ui.ask("Сколько у вас аутсов")
        if not answer.lstrip("-").isdigit():
            ui.bad("Нужно число — считаю как неверный ответ.")
            guess = -99
        else:
            guess = int(answer)

        if abs(guess - len(outs)) <= 1:
            correct += 1
            ui.good("Верно: аутсов %d." % len(outs))
        else:
            ui.bad("Аутсов %d, а не %d." % (len(outs), guess))
        print("     Аутсы: %s" % pretty(sorted(outs, key=lambda c: (-c.rank, c.suit))))
        if ties:
            print("     Ещё %d карт(ы) дают ничью: %s" % (len(ties), pretty(ties)))
        chance = equity(hero, [villain], board, iterations=4000, seed=rng.random())
        print("     Equity до ривера: %.1f%%  (правило 4: ~%d%%)"
              % (chance.hero_equity * 100, min(100, len(outs) * 4)))

    _report(correct, rounds)


def quiz_preflop(rounds: int = 10, rng: Optional[random.Random] = None) -> None:
    """«Играть или сбросить?» — фильтр стартовых рук."""
    rng = rng or random.Random()
    ui.title("Квиз: стартовые руки")
    ui.para("""
        Вам сдали две карты, до вас никто не повышал. Повышать или
        сбрасывать? Ориентир — таблица из урока 6: группы «премиум»,
        «сильная» и «играбельная» играем, «мусор» сбрасываем.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        deck = full_deck()
        rng.shuffle(deck)
        hero = deck[:2]
        notation, tier, advice = ranges.advice_for(hero)

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Ваши карты: %s   (обозначение: %s)" % (pretty(hero), notation))
        print()
        answer = ui.ask_choice("Ваше решение: r — рейз, f — фолд", "rf")
        should_raise = tier != ranges.TIER_FOLD

        if (answer == "r") == should_raise:
            correct += 1
            ui.good("Верно. Группа: %s." % ranges.TIER_NAMES[tier])
        else:
            ui.bad("Группа: %s — здесь правильнее %s."
                   % (ranges.TIER_NAMES[tier], "рейз" if should_raise else "фолд"))
        ui.para(advice, indent=5)
        result = equity(hero, [None], iterations=3000, seed=rng.random())
        print("     Equity против одной случайной руки: %.1f%%"
              % (result.hero_equity * 100))

    _report(correct, rounds)


# --------------------------------------------------------------------------
# Практика решений
# --------------------------------------------------------------------------

def drill_decision(rounds: int = 5, rng: Optional[random.Random] = None) -> None:
    """Колл или фолд: соединяем equity и пот-оддсы в одно решение."""
    rng = rng or random.Random()
    ui.title("Тренажёр: колл или фолд")
    ui.para("""
        Самое важное упражнение в этом скрипте. Карты соперника вам
        открыты — в реальной игре так не бывает, но здесь задача
        не угадать, а научиться сравнивать два числа: вашу equity
        и ту equity, которую требует ставка.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        deck = full_deck()
        rng.shuffle(deck)
        board_size = rng.choice([3, 3, 4])
        hero, villain = deck[:2], deck[2:4]
        board = deck[4:4 + board_size]

        pot = float(rng.choice([60, 80, 100, 120, 160, 200]))
        bet_fraction = rng.choice([0.33, 0.5, 0.5, 0.75, 1.0, 1.5])
        call = round(pot * bet_fraction)
        need = required_equity(pot, call)

        ui.section("Раздача %d из %d" % (round_number, rounds))
        print("  Улица:           %s" % ("флоп" if board_size == 3 else "тёрн"))
        print("  Борд:            %s" % pretty(board))
        print("  Ваши карты:      %s   (%s)" % (pretty(hero), describe(hero + board)))
        print("  Карты соперника: %s   (%s)"
              % (pretty(villain), describe(villain + board)))
        print()
        print("  В банке: %.0f.  Соперник поставил: %.0f." % (pot, call))
        print("  Чтобы продолжить, нужно уравнять %.0f." % call)
        print()
        answer = ui.ask_choice("Ваше решение: c — колл, f — фолд", "cf")

        result = equity(hero, [villain], board, iterations=8000, seed=rng.random())
        should_call = result.hero_equity > need

        print()
        print("  Требуемая equity: %.1f%%   (%.0f / %.0f)" % (need * 100, call, pot + call))
        print("  Ваша equity:      %.1f%%  %s"
              % (result.hero_equity * 100, ui.bar(result.hero_equity, 22)))
        expected_value = result.hero_equity * (pot + call) - call
        print("  Ожидание от колла: %+.1f" % expected_value)

        if (answer == "c") == should_call:
            correct += 1
            ui.good("Верное решение.")
        else:
            ui.bad("Правильнее было %s." % ("коллировать" if should_call else "сбросить"))
        if should_call:
            ui.hint("Колл выгоден: equity выше требуемой на %.1f п.п."
                    % ((result.hero_equity - need) * 100))
        else:
            ui.hint("Колл убыточен: не хватает %.1f п.п. equity."
                    % ((need - result.hero_equity) * 100))

    _report(correct, rounds)


def _report(correct: int, total: int) -> None:
    ui.section("Результат: %d из %d" % (correct, total))
    share = correct / total if total else 0.0
    print("  " + ui.bar(share, 30) + "  %.0f%%" % (share * 100))
    if share == 1.0:
        ui.good("Идеально. Берите следующий тренажёр или увеличьте число вопросов.")
    elif share >= 0.7:
        ui.good("Хороший результат — база есть.")
    elif share >= 0.4:
        ui.hint("Есть над чем поработать: перечитайте уроки 2 и 4.")
    else:
        ui.hint("Пока тяжело — это нормально. Вернитесь к урокам 1-2 "
                "и повторите квиз.")
