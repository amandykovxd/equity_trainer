"""Тренажёры, работающие для любой разновидности покера.

Теория бесполезна, пока решения не доведены до автоматизма. Здесь
программа раздаёт случайные ситуации по правилам выбранной игры,
спрашивает вас и показывает расчёт — чтобы было видно не только
«верно/неверно», но и откуда берётся правильный ответ.
"""
from __future__ import annotations

import random
from typing import List, Optional, Sequence, Tuple

from . import ui
from .cards import Card, pretty
from .equity import equity, next_card_outs, pot_shares, required_equity
from .variant import SPLIT, Variant

Deal = Tuple[List[Card], List[Card]]   # (карты игрока, борд)


# --------------------------------------------------------------------------
# Раздача ситуаций с заданной комбинацией
# --------------------------------------------------------------------------

def straight_windows(variant: Variant) -> List[List[int]]:
    """Все наборы номиналов, образующие стрит в колоде этой игры.

    Для полной колоды это 2-3-4-5-6 ... 10-J-Q-K-A плюс «колесо»
    A-2-3-4-5. Для короткой — 6-7-8-9-10 ... 10-J-Q-K-A плюс A-6-7-8-9,
    потому что младших карт в ней просто нет.
    """
    ranks = sorted({card.rank for card in variant.deck()})
    windows: List[List[int]] = []
    for start in range(len(ranks) - 4):
        window = ranks[start:start + 5]
        if all(window[i + 1] - window[i] == 1 for i in range(4)):
            windows.append(window)
    if 14 in ranks:
        lowest_four = ranks[:4]
        if all(lowest_four[i + 1] - lowest_four[i] == 1 for i in range(3)):
            windows.append(lowest_four + [14])
    return windows


def _core_for_shape(variant: Variant, shape: str, deck: List[Card],
                    rng: random.Random) -> Optional[List[Card]]:
    """Пять карт, из которых скорее всего получится нужная комбинация."""
    by_rank: dict = {}
    by_suit: dict = {}
    for card in deck:
        by_rank.setdefault(card.rank, []).append(card)
        by_suit.setdefault(card.suit, []).append(card)
    ranks = sorted(by_rank)

    if shape == "straight_flush":
        window = rng.choice(straight_windows(variant))
        suit = rng.choice(list(by_suit))
        return [card for rank in window for card in by_rank[rank]
                if card.suit == suit]
    if shape == "quads":
        rank = rng.choice(ranks)
        if len(by_rank[rank]) < 4:
            return None
        rest = [card for card in deck if card.rank != rank]
        return by_rank[rank][:4] + [rng.choice(rest)]
    if shape == "full_house":
        if len(ranks) < 2:
            return None
        trips_rank, pair_rank = rng.sample(ranks, 2)
        if len(by_rank[trips_rank]) < 3 or len(by_rank[pair_rank]) < 2:
            return None
        return by_rank[trips_rank][:3] + by_rank[pair_rank][:2]
    if shape == "flush":
        suit = rng.choice(list(by_suit))
        suited = by_suit[suit]
        if len(suited) < 5:
            return None
        return rng.sample(suited, 5)
    if shape == "straight":
        window = rng.choice(straight_windows(variant))
        return [rng.choice(by_rank[rank]) for rank in window]
    if shape == "trips":
        rank = rng.choice(ranks)
        if len(by_rank[rank]) < 3:
            return None
        rest = [card for card in deck if card.rank != rank]
        return by_rank[rank][:3] + rng.sample(rest, 2)
    if shape == "two_pair":
        if len(ranks) < 3:
            return None
        first, second = rng.sample(ranks, 2)
        rest = [card for card in deck if card.rank not in (first, second)]
        return by_rank[first][:2] + by_rank[second][:2] + [rng.choice(rest)]
    if shape == "pair":
        rank = rng.choice(ranks)
        rest = [card for card in deck if card.rank != rank]
        return by_rank[rank][:2] + rng.sample(rest, 3)
    if shape == "high_card":
        return rng.sample(deck, 5)
    return None


def deal_with_category(variant: Variant, target: int,
                       rng: random.Random) -> Optional[Deal]:
    """Раздача, в которой у игрока получается ровно заданная комбинация.

    Карты-добивки иногда усиливают руку сильнее задуманного (пара
    превращается в две пары), поэтому результат проверяется и при
    несовпадении собирается заново.
    """
    shape = variant.category_shapes[target]
    for _attempt in range(4000):
        deck = variant.deck()
        rng.shuffle(deck)
        core = _core_for_shape(variant, shape, deck, rng)
        if core is None or len(core) != 5:
            continue
        rest = [card for card in deck if card not in set(core)]
        if variant.board_size:
            # Две карты комбинации отдаём в руку, три кладём на борд —
            # так работает и правило «ровно две карты» в омахе.
            hole = core[:2] + rest[:variant.hole_size - 2]
            rest = rest[variant.hole_size - 2:]
            board = core[2:5] + rest[:variant.board_size - 3]
        else:
            hole = core + rest[:variant.hole_size - 5]
            board = []
        if len(hole) != variant.hole_size:
            continue
        try:
            if variant.evaluate_high(hole, board)[0] == target:
                return hole, board
        except (ValueError, KeyError):
            continue
    return None


def deal_two_hands(variant: Variant, rng: random.Random,
                   board_length: Optional[int] = None,
                   hero_cards: Optional[int] = None) -> Tuple[List[Card], List[Card], List[Card]]:
    """Случайная раздача на двоих: (рука героя, рука соперника, борд)."""
    deck = variant.deck()
    rng.shuffle(deck)
    hero_size = variant.hole_size if hero_cards is None else hero_cards
    board_size = variant.board_size if board_length is None else board_length
    hero = deck[:hero_size]
    villain = deck[hero_size:hero_size + variant.hole_size]
    start = hero_size + variant.hole_size
    board = deck[start:start + board_size]
    return hero, villain, board


# --------------------------------------------------------------------------
# Квизы
# --------------------------------------------------------------------------

def quiz_combinations(variant: Variant, rounds: int = 8,
                      rng: Optional[random.Random] = None) -> None:
    """«Что у меня собралось?» — узнавание комбинации."""
    if not variant.category_names:
        ui.bad("В «%s» побеждает слабейшая рука, поэтому квиз на узнавание "
               "комбинаций здесь не нужен. Берите квиз «кто выиграл банк»."
               % variant.name)
        return
    rng = rng or random.Random()
    order = list(variant.category_order)

    ui.title("%s — квиз: назови комбинацию" % variant.name)
    ui.para("""
        Вам показывают вашу руку и, если они есть, общие карты.
        Нужно понять, какая комбинация получилась. Помните: в комбинацию
        входят ровно пять карт — лучшие из доступных.
    """)
    if variant.key == "omaha":
        ui.hint("В омахе работает правило «ровно две карты»: две свои "
                "и три с борда, иначе комбинации нет.")

    correct = 0
    for round_number in range(1, rounds + 1):
        target = rng.choice(order)
        deal = deal_with_category(variant, target, rng)
        if deal is None:
            continue
        hole, board = deal

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Ваши карты: %s" % pretty(hole))
        if board:
            print("  Борд:       %s" % pretty(board))
        print()
        for index, category in enumerate(order, start=1):
            print("    %d) %s" % (index, variant.category_names[category]))
        print()
        answer = ui.ask("Номер ответа")
        chosen = None
        if answer.isdigit() and 1 <= int(answer) <= len(order):
            chosen = order[int(answer) - 1]
        else:
            ui.bad("Нужен номер от 1 до %d — считаю как неверный ответ."
                   % len(order))

        actual = variant.evaluate_high(hole, board)[0]
        if chosen == actual:
            correct += 1
            ui.good("Верно: %s" % variant.describe(hole, board))
        else:
            ui.bad("Правильный ответ: %s" % variant.describe(hole, board))

    report(correct, rounds)


def quiz_showdown(variant: Variant, rounds: int = 8,
                  rng: Optional[random.Random] = None) -> None:
    """«Кто выиграл банк?» — работает для любой разновидности."""
    rng = rng or random.Random()
    ui.title("%s — квиз: кто выиграл банк" % variant.name)
    ui.para("""
        Вскрытие: видны все карты обоих игроков. Определите победителя.
        Это самый полезный квиз: он быстрее всего учит замечать кикеры,
        «общие» комбинации на борде и особенности именно этой игры.
    """)
    if variant.mode == SPLIT:
        ui.para("""
            Здесь банк делится на две половины — хай и лоу. Вариант
            «пополам» означает, что одну половину взял один игрок,
            а другую — другой.
        """)

    correct = 0
    for round_number in range(1, rounds + 1):
        hero, villain, board = deal_two_hands(variant, rng)

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        if board:
            print("  Борд:     %s" % pretty(board))
        print("  Игрок 1:  %s" % pretty(hero))
        print("  Игрок 2:  %s" % pretty(villain))
        print()
        answer = ui.ask_choice(
            "Кто забирает больше? 1 — первый, 2 — второй, s — пополам", "12s")

        shares, had_low = pot_shares(variant, [hero, villain], board)
        if shares[0] > shares[1]:
            truth = "1"
        elif shares[1] > shares[0]:
            truth = "2"
        else:
            truth = "s"

        if answer == truth:
            correct += 1
            ui.good("Верно.")
        else:
            ui.bad("Неверно.")
        print("     Игрок 1: %s" % variant.describe(hero, board))
        print("     Игрок 2: %s" % variant.describe(villain, board))
        print("     Делёж банка: %.0f%% / %.0f%%"
              % (shares[0] * 100, shares[1] * 100))
        if variant.mode == SPLIT and not had_low:
            print("     Лоу ни у кого не собралось — весь банк уходит хай-руке.")

    report(correct, rounds)


def drill_decision(variant: Variant, rounds: int = 5,
                   rng: Optional[random.Random] = None) -> None:
    """Колл или фолд: соединяем equity и пот-оддсы в одно решение."""
    if not variant.supports_next_card_drill:
        ui.bad("В «%s» карты меняют, а не добирают, поэтому ситуации "
               "«осталась одна карта» здесь не бывает. Берите квиз "
               "«кто выиграл банк»." % variant.name)
        return
    rng = rng or random.Random()

    ui.title("%s — тренажёр: колл или фолд" % variant.name)
    ui.para("""
        Самое важное упражнение. Карты соперника вам открыты — в реальной
        игре так не бывает, но здесь задача не угадать, а научиться
        сравнивать два числа: вашу equity и ту equity, которую требует
        ставка соперника.
    """)

    correct = 0
    for round_number in range(1, rounds + 1):
        if variant.board_size:
            board_length = rng.choice([3, 3, 4])
            hero, villain, board = deal_two_hands(variant, rng,
                                                  board_length=board_length)
        else:
            # Герою не хватает одной карты, у соперника рука уже полная.
            hero, villain, board = deal_two_hands(
                variant, rng, hero_cards=variant.hole_size - 1)

        pot = float(rng.choice([60, 80, 100, 120, 160, 200]))
        call = round(pot * rng.choice([0.33, 0.5, 0.5, 0.75, 1.0, 1.5]))
        need = required_equity(pot, call)

        ui.section("Раздача %d из %d" % (round_number, rounds))
        if variant.board_size:
            print("  Улица:           %s" % variant.board_stage(len(board)))
            print("  Борд:            %s" % pretty(board))
        print("  Ваши карты:      %s" % pretty(hero))
        print("  Карты соперника: %s" % pretty(villain))
        print("    у вас:      %s" % variant.describe(hero, board))
        print("    у соперника: %s" % variant.describe(villain, board))
        print()
        print("  В банке %.0f. Соперник поставил %.0f — чтобы продолжить, "
              "нужно уравнять %.0f." % (pot, call, call))
        print()
        answer = ui.ask_choice("Ваше решение: c — колл, f — фолд", "cf")

        result = equity(variant, [hero, villain], board,
                        iterations=max(2000, variant.default_iterations // 4))
        should_call = result.hero_equity > need

        print()
        print("  Требуемая equity: %.1f%%   (%.0f / %.0f)"
              % (need * 100, call, pot + call))
        print("  Ваша equity:      %.1f%%  %s"
              % (result.hero_equity * 100, ui.bar(result.hero_equity, 22)))
        print("  Ожидание колла:   %+.1f"
              % (result.hero_equity * (pot + call) - call))

        if (answer == "c") == should_call:
            correct += 1
            ui.good("Верное решение.")
        else:
            ui.bad("Правильнее было %s."
                   % ("коллировать" if should_call else "сбросить"))
        difference = abs(result.hero_equity - need) * 100
        if should_call:
            ui.hint("Колл выгоден: equity выше требуемой на %.1f п.п."
                    % difference)
        else:
            ui.hint("Колл убыточен: не хватает %.1f п.п. equity." % difference)

    report(correct, rounds)


def report(correct: int, total: int) -> None:
    ui.section("Результат: %d из %d" % (correct, total))
    share = correct / total if total else 0.0
    print("  " + ui.bar(share, 30) + "  %.0f%%" % (share * 100))
    if share == 1.0:
        ui.good("Идеально. Берите следующий тренажёр или увеличьте число "
                "вопросов.")
    elif share >= 0.7:
        ui.good("Хороший результат — база есть.")
    elif share >= 0.4:
        ui.hint("Есть над чем поработать: вернитесь к урокам этой игры.")
    else:
        ui.hint("Пока тяжело — это нормально. Перечитайте правила "
                "и повторите квиз.")
