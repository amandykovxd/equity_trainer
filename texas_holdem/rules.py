"""Правила техасского холдема для движка equity.

2 карманные карты, 5 общих. Комбинация — лучшие 5 карт из этих 7.
Можно использовать обе свои карты, одну или ни одной.
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from core.cards import Card, full_deck
from core.evaluator import (CATEGORY_NAMES_RU, CATEGORY_ORDER,
                            CATEGORY_SHAPES, describe, evaluate)
from core.variant import HIGH, Variant


def evaluate_high(hole: Sequence[Card], board: Sequence[Card]) -> Tuple:
    """Лучшая комбинация из любых пяти карт среди своих и общих."""
    return evaluate(tuple(hole) + tuple(board))


def describe_high(hole: Sequence[Card], board: Sequence[Card]) -> str:
    cards = tuple(hole) + tuple(board)
    if len(cards) < 5:
        return "комбинации ещё нет — карт меньше пяти"
    return describe(cards)


VARIANT = Variant(
    key="texas_holdem",
    name="Техасский холдем",
    short_description="2 своих карты, 5 общих, лучшая комбинация из 7 — "
                      "самая популярная игра в мире",
    hole_size=2,
    board_size=5,
    deck=full_deck,
    mode=HIGH,
    evaluate_high=evaluate_high,
    describe_high=describe_high,
    streets=("префлоп", "флоп", "тёрн", "ривер"),
    terms=("texas_holdem", "hole_cards", "board", "kicker", "outs", "pot_odds"),
    category_names=CATEGORY_NAMES_RU,
    category_order=CATEGORY_ORDER,
    category_shapes=CATEGORY_SHAPES,
    typical_players="2-9",
    default_iterations=25_000,
)
