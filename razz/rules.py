"""Правила разза для движка equity.

Разз — это семикарточный стад наоборот: банк забирает самая СЛАБАЯ
рука. Используется система A-5:

  • туз — младшая карта (считается за единицу);
  • стриты и флеши не считаются вообще, они не портят и не улучшают руку;
  • пары, тройки и каре — плохо: они делают руку хуже любой руки
    без пар;
  • лучшая возможная рука — 5-4-3-2-A («колесо»).

Руку называют по двум старшим картам: 8-6-5-3-A — это «восьмёрка-шесть»,
и она слабее (то есть лучше), чем 8-7-2-3-A.
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from core.cards import Card, full_deck
from core.lowball import ace_to_five, describe_ace_to_five
from core.variant import LOW, Variant


def evaluate_low(hole: Sequence[Card], board: Sequence[Card]) -> Optional[Tuple]:
    return ace_to_five(tuple(hole))


def describe_low(hole: Sequence[Card], board: Sequence[Card]) -> str:
    if len(hole) < 5:
        return "лоу ещё не собрано — карт меньше пяти"
    return describe_ace_to_five(tuple(hole))


VARIANT = Variant(
    key="razz",
    name="Разз",
    short_description="стад, где побеждает самая слабая рука; "
                      "лучшая рука — 5-4-3-2-A",
    hole_size=7,
    board_size=0,
    deck=full_deck,
    mode=LOW,
    evaluate_low=evaluate_low,
    describe_low=describe_low,
    streets=("3-я улица", "4-я улица", "5-я улица", "6-я улица", "7-я улица"),
    terms=("razz", "nut_low", "wheel", "door_card", "bring_in", "dead_cards"),
    typical_players="2-8",
    default_iterations=20_000,
)
