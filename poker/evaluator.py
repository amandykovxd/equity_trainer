"""Оценка силы покерной комбинации.

Главная функция — evaluate(): берёт 5, 6 или 7 карт и возвращает «оценку» —
кортеж, который можно просто сравнивать оператором >. Чем больше кортеж,
тем сильнее рука. Равные кортежи = ничья (в покере это называется «сплит»).

Первый элемент кортежа — категория комбинации (8 = флеш-рояль/стрит-флеш,
0 = просто старшая карта), дальше идут карты для разрешения спора при
одинаковых категориях («кикеры»).
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Iterable, List, Sequence, Tuple

from .cards import Card, RANK_GENITIVE_RU, RANK_NAMES_RU, RANK_PLURAL_RU, VALUE_CHARS

# Категории от сильной к слабой.
STRAIGHT_FLUSH = 8
FOUR_OF_A_KIND = 7
FULL_HOUSE = 6
FLUSH = 5
STRAIGHT = 4
THREE_OF_A_KIND = 3
TWO_PAIR = 2
ONE_PAIR = 1
HIGH_CARD = 0

CATEGORY_NAMES_RU = {
    STRAIGHT_FLUSH: "Стрит-флеш",
    FOUR_OF_A_KIND: "Каре",
    FULL_HOUSE: "Фулл-хаус",
    FLUSH: "Флеш",
    STRAIGHT: "Стрит",
    THREE_OF_A_KIND: "Сет (тройка)",
    TWO_PAIR: "Две пары",
    ONE_PAIR: "Пара",
    HIGH_CARD: "Старшая карта",
}

Score = Tuple[int, ...]


def _straight_high(ranks: Iterable[int]) -> int:
    """Старшая карта стрита или 0, если стрита нет.

    Туз умеет быть и старшим, и младшим: A-2-3-4-5 — это тоже стрит
    (его называют «колесо»), и в нём туз считается за единицу.
    """
    present = set(ranks)
    if 14 in present:
        present.add(1)
    for high in range(14, 4, -1):
        if all(high - offset in present for offset in range(5)):
            return high
    return 0


def evaluate(cards: Sequence[Card]) -> Score:
    """Оценка лучшей пятикарточной комбинации из переданных карт."""
    rank_counts = Counter(card.rank for card in cards)
    suit_counts = Counter(card.suit for card in cards)

    # --- Флеш и стрит-флеш ---
    # Если пять карт одной масти есть, то каре и фулл-хаус уже невозможны
    # (на них просто не хватит карт), поэтому можно отвечать сразу.
    for suit, count in suit_counts.items():
        if count >= 5:
            flush_ranks = sorted(
                (card.rank for card in cards if card.suit == suit), reverse=True
            )
            high = _straight_high(flush_ranks)
            if high:
                return (STRAIGHT_FLUSH, high)
            return (FLUSH,) + tuple(flush_ranks[:5])

    # Номиналы, сгруппированные по количеству: сначала самые частые,
    # внутри одинакового количества — старшие.
    groups: List[Tuple[int, int]] = sorted(
        rank_counts.items(), key=lambda item: (-item[1], -item[0])
    )
    ordered_ranks = sorted((card.rank for card in cards), reverse=True)

    def kickers(exclude: Sequence[int], how_many: int) -> Tuple[int, ...]:
        rest = [r for r in ordered_ranks if r not in exclude]
        return tuple(rest[:how_many])

    top_rank, top_count = groups[0]

    if top_count == 4:
        return (FOUR_OF_A_KIND, top_rank) + kickers([top_rank], 1)

    if top_count == 3:
        pair_rank = next((r for r, c in groups[1:] if c >= 2), 0)
        if pair_rank:
            return (FULL_HOUSE, top_rank, pair_rank)

    straight_high = _straight_high(ordered_ranks)
    if straight_high:
        return (STRAIGHT, straight_high)

    if top_count == 3:
        return (THREE_OF_A_KIND, top_rank) + kickers([top_rank], 2)

    if top_count == 2:
        pairs = [r for r, c in groups if c == 2]
        if len(pairs) >= 2:
            high_pair, low_pair = pairs[0], pairs[1]
            return (TWO_PAIR, high_pair, low_pair) + kickers([high_pair, low_pair], 1)
        return (ONE_PAIR, top_rank) + kickers([top_rank], 3)

    return (HIGH_CARD,) + tuple(ordered_ranks[:5])


def best_five(cards: Sequence[Card]) -> List[Card]:
    """Какие именно пять карт образуют комбинацию.

    Нужно только для объяснений человеку, поэтому можно не экономить:
    перебираем все варианты по пять карт и берём лучший.
    """
    if len(cards) <= 5:
        return list(cards)
    return list(max(combinations(cards, 5), key=evaluate))


def category_of(cards: Sequence[Card]) -> int:
    return evaluate(cards)[0]


def describe(cards: Sequence[Card]) -> str:
    """Человеческое название комбинации: «Пара королей», «Флеш до туза»."""
    score = evaluate(cards)
    category = score[0]
    name = CATEGORY_NAMES_RU[category]

    if category == STRAIGHT_FLUSH:
        if score[1] == 14:
            return "Флеш-рояль (стрит-флеш до туза) — сильнейшая рука в покере"
        return "%s до %s" % (name, RANK_GENITIVE_RU[score[1]])
    if category == FOUR_OF_A_KIND:
        return "%s %s" % (name, RANK_PLURAL_RU[score[1]])
    if category == FULL_HOUSE:
        return "%s: три %s и пара %s" % (
            name, RANK_GENITIVE_RU[score[1]], RANK_PLURAL_RU[score[2]],
        )
    if category == FLUSH:
        return "%s до %s" % (name, RANK_GENITIVE_RU[score[1]])
    if category == STRAIGHT:
        if score[1] == 5:
            return "%s A-2-3-4-5 («колесо»)" % name
        return "%s до %s" % (name, RANK_GENITIVE_RU[score[1]])
    if category == THREE_OF_A_KIND:
        return "%s: три %s" % (name, RANK_GENITIVE_RU[score[1]])
    if category == TWO_PAIR:
        return "%s: %s и %s" % (
            name, RANK_PLURAL_RU[score[1]], RANK_PLURAL_RU[score[2]],
        )
    if category == ONE_PAIR:
        return "%s %s" % (name, RANK_PLURAL_RU[score[1]])
    return "%s — %s" % (name, RANK_NAMES_RU[score[1]])


def compare(left: Sequence[Card], right: Sequence[Card]) -> int:
    """1 — левая рука сильнее, -1 — правая, 0 — ничья."""
    left_score, right_score = evaluate(left), evaluate(right)
    if left_score > right_score:
        return 1
    if left_score < right_score:
        return -1
    return 0


def score_to_text(score: Score) -> str:
    """Отладочное представление оценки."""
    tail = " ".join(VALUE_CHARS.get(value, str(value)) for value in score[1:])
    return "%s (%s)" % (CATEGORY_NAMES_RU[score[0]], tail)
