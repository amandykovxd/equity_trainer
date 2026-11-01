"""Правила семикарточного стада для движка equity.

Общих карт нет совсем. Каждый игрок получает свои 7 карт, и комбинация
собирается из лучших 5 из них — порядок старшинства обычный.

Как раздаются 7 карт (и почему это важно):
  3-я улица — две закрытые карты и одна открытая («дор-карта»);
  4-я, 5-я, 6-я улицы — по одной открытой карте;
  7-я улица — последняя карта, закрытая.

То есть четыре из семи карт соперника вы видите своими глазами. Главный
навык в стаде — помнить, какие карты уже открылись: если три нужные вам
карты лежат у соперников, ваше дро мертво, сколько бы аутсов
ни казалось по учебнику.
"""
from __future__ import annotations

from typing import Sequence, Tuple

from core.cards import Card, full_deck
from core.evaluator import (CATEGORY_NAMES_RU, CATEGORY_ORDER,
                            CATEGORY_SHAPES, describe, evaluate)
from core.variant import HIGH, Variant


def evaluate_high(hole: Sequence[Card], board: Sequence[Card]) -> Tuple:
    # Борда в стаде нет: в комбинацию идут только свои карты.
    return evaluate(tuple(hole))


def describe_high(hole: Sequence[Card], board: Sequence[Card]) -> str:
    if len(hole) < 5:
        return "комбинации ещё нет — карт меньше пяти"
    return describe(tuple(hole))


VARIANT = Variant(
    key="seven_card_stud",
    name="Семикарточный стад",
    short_description="общих карт нет: у каждого свои 7 карт, часть "
                      "из них открыта для всех",
    hole_size=7,
    board_size=0,
    deck=full_deck,
    mode=HIGH,
    evaluate_high=evaluate_high,
    describe_high=describe_high,
    streets=("3-я улица", "4-я улица", "5-я улица", "6-я улица", "7-я улица"),
    terms=("seven_card_stud", "door_card", "bring_in", "dead_cards",
           "ante", "fixed_limit"),
    category_names=CATEGORY_NAMES_RU,
    category_order=CATEGORY_ORDER,
    category_shapes=CATEGORY_SHAPES,
    typical_players="2-8",
    default_iterations=20_000,
)
