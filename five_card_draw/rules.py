"""Правила пятикарточного дро для движка equity.

Самая простая разновидность — в неё обычно играют дома.

  • Каждому сдают 5 закрытых карт.
  • Круг ставок.
  • Замена: можно сбросить любое число своих карт и взять столько же
    новых. Отказ от замены называется «пэт».
  • Ещё круг ставок, затем вскрытие.

Общих карт нет, и о сопернике известно почти ничего — только сколько
карт он поменял. Поменял три — скорее всего держал пару. Не менял
вовсе — заявляет готовую руку.
"""
from __future__ import annotations

from typing import Sequence, Tuple

from core.cards import Card, full_deck
from core.evaluator import (CATEGORY_NAMES_RU, CATEGORY_ORDER,
                            CATEGORY_SHAPES, describe, evaluate)
from core.variant import HIGH, Variant


def evaluate_high(hole: Sequence[Card], board: Sequence[Card]) -> Tuple:
    return evaluate(tuple(hole))


def describe_high(hole: Sequence[Card], board: Sequence[Card]) -> str:
    if len(hole) < 5:
        return "комбинации ещё нет — карт меньше пяти"
    return describe(tuple(hole))


VARIANT = Variant(
    key="five_card_draw",
    name="Пятикарточный дро",
    short_description="5 закрытых карт и замена; общих карт нет — "
                      "самые простые правила",
    hole_size=5,
    board_size=0,
    deck=full_deck,
    mode=HIGH,
    evaluate_high=evaluate_high,
    describe_high=describe_high,
    streets=("до замены", "после замены"),
    terms=("five_card_draw", "stand_pat", "draw", "bluff"),
    category_names=CATEGORY_NAMES_RU,
    category_order=CATEGORY_ORDER,
    category_shapes=CATEGORY_SHAPES,
    supports_next_card_drill=False,
    typical_players="2-6",
    default_iterations=20_000,
)
