"""Стартовые руки: как обозначаются и какие из них стоит играть.

169 стартовых рук техасского холдема обозначают тремя символами:
  AA   — пара (масти не важны);
  AKs  — s = suited, одномастные (A и K одной масти);
  AKo  — o = offsuit, разной масти.

Одномастные руки чуть сильнее: они могут собрать флеш.

Группы ниже — умышленно упрощённый ориентир для новичка, а не
«решение» игры. Задача — не выучить таблицу, а привыкнуть
сбрасывать мусор до флопа: именно на слабых стартовых руках
новички теряют больше всего.
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .cards import Card, RANK_CHARS, VALUE_CHARS

PREMIUM = "AA KK QQ JJ AKs AKo AQs".split()

STRONG = "TT 99 AQo AJs ATs KQs KJs QJs KQo".split()

PLAYABLE = (
    "88 77 66 55 44 33 22 "
    "A9s A8s A7s A6s A5s A4s A3s A2s "
    "KTs K9s QTs Q9s JTs J9s T9s T8s 98s 97s 87s 76s 65s 54s "
    "AJo ATo KJo KTo QJo QTo JTo"
).split()

TIER_PREMIUM, TIER_STRONG, TIER_PLAYABLE, TIER_FOLD = 0, 1, 2, 3

TIER_NAMES = {
    TIER_PREMIUM: "Премиум",
    TIER_STRONG: "Сильная",
    TIER_PLAYABLE: "Играбельная",
    TIER_FOLD: "Мусор",
}

TIER_ADVICE = {
    TIER_PREMIUM: "Повышайте всегда и с любой позиции. Таких рук мало — "
                  "не разыгрывайте их пассивно.",
    TIER_STRONG: "Повышайте. Но если соперник отвечает большим рейзом, "
                 "будьте готовы расстаться с рукой.",
    TIER_PLAYABLE: "Играйте с поздней позиции или против одного соперника. "
                   "С ранней позиции такие руки проще сбросить.",
    TIER_FOLD: "Сбрасывайте до флопа. Это не трусость, а основной источник "
               "вашей прибыли в будущем.",
}

_TIER_BY_HAND: Dict[str, int] = {}
for _hand in PREMIUM:
    _TIER_BY_HAND[_hand] = TIER_PREMIUM
for _hand in STRONG:
    _TIER_BY_HAND[_hand] = TIER_STRONG
for _hand in PLAYABLE:
    _TIER_BY_HAND[_hand] = TIER_PLAYABLE


def hand_notation(cards: Sequence[Card]) -> str:
    """Два карты → короткое обозначение: AsKs → «AKs», 7h7d → «77»."""
    if len(cards) != 2:
        raise ValueError("Стартовая рука — это ровно 2 карты.")
    high, low = sorted((card.rank for card in cards), reverse=True)
    if high == low:
        return VALUE_CHARS[high] * 2
    suffix = "s" if cards[0].suit == cards[1].suit else "o"
    return VALUE_CHARS[high] + VALUE_CHARS[low] + suffix


def tier_of(notation: str) -> int:
    return _TIER_BY_HAND.get(notation, TIER_FOLD)


def advice_for(cards: Sequence[Card]) -> Tuple[str, int, str]:
    """(обозначение, группа, совет) для конкретной пары карт."""
    notation = hand_notation(cards)
    tier = tier_of(notation)
    return notation, tier, TIER_ADVICE[tier]


def chart_rows() -> List[List[Tuple[str, int]]]:
    """Таблица 13×13: по диагонали пары, выше — одномастные, ниже — разномастные."""
    order = list(reversed(RANK_CHARS))  # A, K, Q, ... 2
    rows: List[List[Tuple[str, int]]] = []
    for row_index, row_rank in enumerate(order):
        row: List[Tuple[str, int]] = []
        for column_index, column_rank in enumerate(order):
            if row_index == column_index:
                notation = row_rank * 2
            elif column_index > row_index:
                notation = row_rank + column_rank + "s"
            else:
                notation = column_rank + row_rank + "o"
            row.append((notation, tier_of(notation)))
        rows.append(row)
    return rows
