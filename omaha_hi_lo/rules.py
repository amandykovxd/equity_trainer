"""Правила омахи хай-лоу (Omaha/8) для движка equity.

Как обычная омаха: 4 своих карты, 5 общих, в комбинации ровно 2 своих
и ровно 3 общих. Отличие одно, но большое: банк делится на две половины.

  Хай — забирает сильнейшая комбинация, как обычно.
  Лоу — забирает слабейшая рука по системе A-5, но только если она
        проходит квалификацию: пять РАЗНЫХ карт достоинством
        8 или ниже (туз считается за единицу).

Если лоу не собралось ни у кого, весь банк уходит хай-руке. Забрать
обе половины называется «скуп» — именно к этому и стремятся.

Важная тонкость: хай и лоу можно собирать РАЗНЫМИ парами своих карт.
Правило «ровно две» применяется к каждой половине отдельно.
"""
from __future__ import annotations

from itertools import combinations
from typing import Optional, Sequence, Tuple

from core.cards import Card, full_deck
from core.evaluator import describe, evaluate
from core.lowball import QUALIFIER, eight_or_better, hand_text, low_rank
from core.variant import SPLIT, Variant


def best_high(hole: Sequence[Card], board: Sequence[Card]):
    if len(hole) < 2 or len(board) < 3:
        return None
    best = best_cards = None
    for two in combinations(hole, 2):
        for three in combinations(board, 3):
            score = evaluate(two + three)
            if best is None or score > best:
                best, best_cards = score, two + three
    return best, best_cards


def best_low(hole: Sequence[Card], board: Sequence[Card]):
    """Лучшее лоу из ровно двух своих и ровно трёх общих карт."""
    if len(hole) < 2 or len(board) < 3:
        return None
    best = best_cards = None
    for two in combinations(hole, 2):
        for three in combinations(board, 3):
            score = eight_or_better(two + three)
            if score is not None and (best is None or score < best):
                best, best_cards = score, two + three
    if best is None:
        return None
    return best, best_cards


def evaluate_high(hole: Sequence[Card], board: Sequence[Card]) -> Tuple:
    result = best_high(hole, board)
    if result is None:
        raise ValueError("Нужно минимум 2 своих карты и 3 общих.")
    return result[0]


def evaluate_low(hole: Sequence[Card], board: Sequence[Card]) -> Optional[Tuple]:
    """Быстрая оценка лоу: работает с номиналами, а не с картами.

    Нужны пять РАЗНЫХ достоинств не старше восьмёрки: два из руки
    и три с борда. Одинаковые достоинства дают пару, а пара лоу
    не считается — поэтому дубликаты сразу отбрасываются.
    """
    hole_low = sorted({low_rank(card) for card in hole if low_rank(card) <= QUALIFIER})
    board_low = sorted({low_rank(card) for card in board if low_rank(card) <= QUALIFIER})
    if len(hole_low) < 2 or len(board_low) < 3:
        return None
    best = None
    for two in combinations(hole_low, 2):
        for three in combinations(board_low, 3):
            ranks = set(two) | set(three)
            if len(ranks) != 5:
                continue
            score = tuple(sorted(ranks, reverse=True))
            if best is None or score < best:
                best = score
    return best


def describe_high(hole: Sequence[Card], board: Sequence[Card]) -> str:
    result = best_high(hole, board)
    if result is None:
        return "хай: комбинации ещё нет"
    return "Хай: %s" % describe(result[1])


def describe_low(hole: Sequence[Card], board: Sequence[Card]) -> str:
    result = best_low(hole, board)
    if result is None:
        if len(board) < 3:
            return "лоу: ещё не определено"
        return "Лоу не собрано (нужно 5 разных карт от восьмёрки и ниже)"
    from core.cards import pretty
    return "Лоу %s — играют %s" % (hand_text(result[0]), pretty(result[1]))


VARIANT = Variant(
    key="omaha_hi_lo",
    name="Омаха хай-лоу (Omaha/8)",
    short_description="омаха, где банк делится между сильнейшей рукой "
                      "и слабейшей (если лоу вообще собралось)",
    hole_size=4,
    board_size=5,
    deck=full_deck,
    mode=SPLIT,
    evaluate_high=evaluate_high,
    evaluate_low=evaluate_low,
    describe_high=describe_high,
    describe_low=describe_low,
    streets=("префлоп", "флоп", "тёрн", "ривер"),
    terms=("omaha_hi_lo", "exactly_two", "qualifier", "scoop", "nut_low",
           "counterfeit", "split", "wheel"),
    typical_players="2-9",
    default_iterations=6_000,
)
