"""Правила лоуболла 2-7 для движка equity.

Пятикарточный дро, в котором побеждает самая слабая рука — но система
оценки здесь совсем другая, чем в раззе:

  • туз СТАРШИЙ (то есть худшая карта для лоу);
  • стриты и флеши считаются — и портят руку;
  • лучшая возможная рука — 7-5-4-3-2 разных мастей.

Почему не 6-5-4-3-2? Потому что это стрит, а стрит в 2-7 — сильная
комбинация, то есть плохая. И почему не 7-5-4-3-2 одной масти?
Потому что это флеш, то же самое.

Версия с тремя кругами замены называется трипл-дро — она и
распространена в онлайне.
"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from core.cards import Card, full_deck
from core.lowball import deuce_to_seven, describe_deuce_to_seven
from core.variant import LOW, Variant


def evaluate_low(hole: Sequence[Card], board: Sequence[Card]) -> Optional[Tuple]:
    return deuce_to_seven(tuple(hole))


def describe_low(hole: Sequence[Card], board: Sequence[Card]) -> str:
    if len(hole) < 5:
        return "рука ещё не собрана — карт меньше пяти"
    return describe_deuce_to_seven(tuple(hole))


VARIANT = Variant(
    key="deuce_to_seven",
    name="Лоуболл 2-7 (трипл-дро)",
    short_description="дро-покер, где побеждает слабейшая рука, но стриты "
                      "и флеши считаются; лучшая рука — 7-5-4-3-2",
    hole_size=5,
    board_size=0,
    deck=full_deck,
    mode=LOW,
    evaluate_low=evaluate_low,
    describe_low=describe_low,
    streets=("до 1-й замены", "после 1-й", "после 2-й", "после 3-й"),
    terms=("deuce_to_seven", "stand_pat", "draw", "fixed_limit"),
    supports_next_card_drill=False,
    typical_players="2-6",
    default_iterations=20_000,
)
