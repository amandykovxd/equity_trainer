"""Правила бадуги для движка equity.

У каждого 4 карты, общих карт нет, есть круги замены. Побеждает самая
низкая рука, в которой все карты РАЗНЫХ мастей и РАЗНЫХ достоинств.

  • Такая рука из четырёх карт называется «бадуги».
  • Если полного набора нет, рука считается по трём подходящим картам
    («снаут»), и любое бадуги бьёт любой снаут.
  • Туз — младшая карта.
  • Лучшая возможная рука — 4-3-2-A всех четырёх мастей.

Пример: 7♠ 5♥ 3♦ 2♣ — это бадуги (все масти и номиналы разные).
А 7♠ 5♥ 5♦ 2♣ — только снаут 7-5-2, потому что две пятёрки
одновременно не работают.
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from core.cards import Card, full_deck
from core.lowball import badugi, describe_badugi
from core.variant import LOW, Variant


def evaluate_low(hole: Sequence[Card], board: Sequence[Card]) -> Optional[Tuple]:
    return badugi(tuple(hole))


def describe_low(hole: Sequence[Card], board: Sequence[Card]) -> str:
    if not hole:
        return "карт нет"
    return describe_badugi(tuple(hole))


VARIANT = Variant(
    key="badugi",
    name="Бадуги",
    short_description="4 карты, побеждает самая низкая рука из карт разных "
                      "мастей и разных достоинств; лучшая — 4-3-2-A",
    hole_size=4,
    board_size=0,
    deck=full_deck,
    mode=LOW,
    evaluate_low=evaluate_low,
    describe_low=describe_low,
    streets=("до 1-й замены", "после 1-й", "после 2-й", "после 3-й"),
    terms=("badugi", "snowman", "stand_pat", "draw"),
    supports_next_card_drill=False,
    typical_players="2-6",
    default_iterations=20_000,
)
