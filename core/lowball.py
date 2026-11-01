"""Оценка «низких» рук — для игр, где побеждает слабейшая комбинация.

Таких систем в покере несколько, и они различаются сильнее, чем кажется:

  A-5 («от туза к пятёрке») — разз, лоу-половина в хай-лоу.
      Туз — младшая карта. Стриты и флеши не считаются вообще.
      Лучшая рука: 5-4-3-2-A («колесо»).

  8 or better — та же система, но лоу вообще не считается собранным,
      если в нём нет пяти разных карт достоинством 8 или ниже.

  2-7 («от двойки к семёрке») — лоуболл 2-7 и трипл-дро.
      Туз — старшая карта. Стриты и флеши считаются и портят руку.
      Лучшая рука: 7-5-4-3-2 разных мастей.

  Бадуги — побеждает рука из четырёх карт разных мастей и разных
      достоинств. Лучшая: 4-3-2-A всех четырёх мастей.

Во всех функциях ниже МЕНЬШЕЕ значение означает БОЛЕЕ СИЛЬНУЮ руку —
это противоположно обычной оценке из evaluator.py.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import List, Optional, Sequence, Tuple

from .cards import Card, RANK_PLURAL_RU, VALUE_CHARS
from .evaluator import evaluate

LowScore = Tuple[int, ...]

# Форма руки (сколько карт каждого достоинства) → категория.
# Стритов и флешей в системе A-5 не существует, поэтому их здесь нет.
SHAPE_CATEGORIES = {
    (1, 1, 1, 1, 1): 0,  # все карты разные — лучшая форма для лоу
    (2, 1, 1, 1): 1,     # пара
    (2, 2, 1): 2,        # две пары
    (3, 1, 1): 3,        # тройка
    (3, 2): 4,           # фулл-хаус
    (4, 1): 5,           # каре — худшее, что может случиться с лоу
}

CATEGORY_NAMES_LOW = {
    0: "лоу", 1: "пара", 2: "две пары", 3: "тройка",
    4: "фулл-хаус", 5: "каре",
}


def low_rank(card: Card) -> int:
    """Достоинство карты в системе, где туз младший: туз становится единицей."""
    return 1 if card.rank == 14 else card.rank


def _rank_text(rank: int) -> str:
    return "A" if rank == 1 else VALUE_CHARS[rank]


def hand_text(ranks: Sequence[int]) -> str:
    """«8-6-4-3-A» — привычная запись лоу-руки."""
    return "-".join(_rank_text(rank) for rank in ranks)


# --------------------------------------------------------------------------
# Система A-5: разз и лоу-половина в хай-лоу
# --------------------------------------------------------------------------

def ace_to_five_five(cards: Sequence[Card]) -> LowScore:
    """Оценка ровно пяти карт по системе A-5. Меньше — лучше."""
    ranks = [low_rank(card) for card in cards]
    counts = Counter(ranks)
    shape = tuple(sorted(counts.values(), reverse=True))
    category = SHAPE_CATEGORIES[shape]
    # Порядок тот же, что в обычной оценке: сначала самые частые
    # достоинства, внутри — старшие. Но сравнение идёт «меньше — лучше».
    ordered: List[int] = []
    for rank, count in sorted(counts.items(), key=lambda item: (-item[1], -item[0])):
        ordered.extend([rank] * count)
    return (category,) + tuple(ordered)


def ace_to_five(cards: Sequence[Card]) -> LowScore:
    """Лучшая (то есть самая низкая) пятёрка из любого числа карт."""
    if len(cards) < 5:
        raise ValueError("Для лоу нужно минимум 5 карт, передано %d." % len(cards))
    if len(cards) == 5:
        return ace_to_five_five(cards)
    return min(ace_to_five_five(five) for five in combinations(cards, 5))


def describe_ace_to_five(cards: Sequence[Card]) -> str:
    score = ace_to_five(cards)
    category, ranks = score[0], score[1:]
    if category == 0:
        return "Лоу %s (старшая %s)" % (hand_text(ranks), _rank_text(ranks[0]))
    return "%s %s — плохое лоу: %s" % (
        CATEGORY_NAMES_LOW[category].capitalize(),
        RANK_PLURAL_RU[14 if ranks[0] == 1 else ranks[0]],
        hand_text(ranks),
    )


# --------------------------------------------------------------------------
# Квалификация «восьмёрка или ниже» — лоу в хай-лоу играх
# --------------------------------------------------------------------------

QUALIFIER = 8


def eight_or_better(cards: Sequence[Card]) -> Optional[LowScore]:
    """Лоу по правилу «8 or better», или None, если лоу не собрано.

    Нужны пять карт разных достоинств, каждая не старше восьмёрки
    (туз считается за единицу). Масти не важны.
    """
    low_ranks = sorted({low_rank(card) for card in cards
                        if low_rank(card) <= QUALIFIER})
    if len(low_ranks) < 5:
        return None
    return tuple(reversed(low_ranks[:5]))


def describe_eight_or_better(cards: Sequence[Card]) -> str:
    score = eight_or_better(cards)
    if score is None:
        return "Лоу не собрано (нужно 5 разных карт от восьмёрки и ниже)"
    return "Лоу %s" % hand_text(score)


# --------------------------------------------------------------------------
# Система 2-7: лоуболл, где стриты и флеши портят руку
# --------------------------------------------------------------------------

def deuce_to_seven(cards: Sequence[Card]) -> LowScore:
    """Оценка по системе 2-7. Меньше — лучше.

    Это обычная оценка старшей руки (туз старший, стриты и флеши
    считаются), только побеждает теперь самая слабая.
    """
    if len(cards) < 5:
        raise ValueError("Нужно минимум 5 карт, передано %d." % len(cards))
    if len(cards) == 5:
        return evaluate(cards, wheel=False)
    return min(evaluate(five, wheel=False) for five in combinations(cards, 5))


def describe_deuce_to_seven(cards: Sequence[Card]) -> str:
    from .evaluator import HIGH_CARD
    from .evaluator import describe as describe_high

    if len(cards) == 5:
        best = tuple(cards)
    else:
        best = min(combinations(cards, 5),
                   key=lambda five: evaluate(five, wheel=False))
    score = evaluate(best, wheel=False)
    if score[0] == HIGH_CARD:
        ranks = hand_text(score[1:])
        if score[1:] == (7, 5, 4, 3, 2):
            return "Лоу %s — лучшая возможная рука в 2-7" % ranks
        return "Лоу %s (старшая %s)" % (ranks, _rank_text(score[1]))
    # Пара, стрит, флеш и всё прочее в 2-7 только портят руку.
    return "%s — в 2-7 это плохо" % describe_high(best)


# --------------------------------------------------------------------------
# Бадуги
# --------------------------------------------------------------------------

def badugi(cards: Sequence[Card]) -> LowScore:
    """Оценка руки в бадуги. Меньше — лучше.

    Ищем самый большой набор карт, в котором все достоинства разные
    И все масти разные. Четыре таких карты называются «бадуги»,
    три — «снаут». Среди наборов одного размера лучше тот, где карты
    младше.
    """
    best: Optional[LowScore] = None
    for size in range(min(4, len(cards)), 0, -1):
        for subset in combinations(cards, size):
            ranks = [low_rank(card) for card in subset]
            suits = [card.suit for card in subset]
            if len(set(ranks)) != size or len(set(suits)) != size:
                continue
            score = (4 - size,) + tuple(sorted(ranks, reverse=True))
            if best is None or score < best:
                best = score
        if best is not None:
            break   # набор большего размера всегда сильнее меньшего
    return best if best is not None else (4,)


BADUGI_SIZE_NAMES = {
    4: "бадуги (4 карты)",
    3: "снаут (3 карты)",
    2: "2 карты",
    1: "1 карта",
}


def describe_badugi(cards: Sequence[Card]) -> str:
    score = badugi(cards)
    size = 4 - score[0]
    ranks = hand_text(score[1:])
    if size == 4:
        if score[1:] == (4, 3, 2, 1):
            return "Бадуги %s — лучшая возможная рука" % ranks
        return "Бадуги %s" % ranks
    return "%s: %s — бадуги не собрано" % (BADUGI_SIZE_NAMES[size].capitalize(), ranks)
