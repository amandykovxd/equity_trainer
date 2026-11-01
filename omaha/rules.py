"""Правила омахи для движка equity.

4 карманные карты, 5 общих. Главное отличие от холдема: комбинация
собирается из РОВНО двух своих карт и РОВНО трёх общих. Ни одну,
ни три свои карты использовать нельзя.

Отсюда следует то, на чём новички ошибаются постоянно: если на борде
четыре карты одной масти, а у вас одна карта этой масти — флеша у вас
нет, потому что вторую взять неоткуда.
"""
from __future__ import annotations

from itertools import combinations
from typing import Optional, Sequence, Tuple

from core.cards import Card, full_deck
from core.evaluator import (CATEGORY_NAMES_RU, CATEGORY_ORDER,
                            CATEGORY_SHAPES, describe, evaluate)
from core.variant import HIGH, Variant


def best_five(hole: Sequence[Card], board: Sequence[Card]) -> Optional[Tuple]:
    """Лучшая пятёрка: ровно 2 карты из руки + ровно 3 с борда."""
    if len(hole) < 2 or len(board) < 3:
        return None
    best = None
    best_cards = None
    for two in combinations(hole, 2):
        for three in combinations(board, 3):
            score = evaluate(two + three)
            if best is None or score > best:
                best, best_cards = score, two + three
    return best, best_cards


def evaluate_high(hole: Sequence[Card], board: Sequence[Card]) -> Tuple:
    result = best_five(hole, board)
    if result is None:
        raise ValueError("Для комбинации в омахе нужно минимум 2 своих "
                         "карты и 3 общих.")
    return result[0]


def describe_high(hole: Sequence[Card], board: Sequence[Card]) -> str:
    result = best_five(hole, board)
    if result is None:
        return "комбинации ещё нет — нужно минимум 3 общие карты"
    from core.cards import pretty
    return "%s — играют %s" % (describe(result[1]), pretty(result[1]))


VARIANT = Variant(
    key="omaha",
    name="Омаха (PLO)",
    short_description="4 своих карты, 5 общих, в комбинации — ровно 2 своих "
                      "и ровно 3 общих",
    hole_size=4,
    board_size=5,
    deck=full_deck,
    mode=HIGH,
    evaluate_high=evaluate_high,
    describe_high=describe_high,
    streets=("префлоп", "флоп", "тёрн", "ривер"),
    terms=("omaha", "exactly_two", "wrap", "blocker", "nuts", "pot_limit"),
    category_names=CATEGORY_NAMES_RU,
    category_order=CATEGORY_ORDER,
    category_shapes=CATEGORY_SHAPES,
    typical_players="2-9",
    # Оценка одной руки перебирает 60 вариантов, поэтому раздач меньше.
    default_iterations=8_000,
)
