"""Правила шортдек-холдема (Six Plus Hold'em) для движка equity.

Играется как обычный холдем, но колода короткая: все карты младше
шестёрки убраны, остаётся 36 карт (6, 7, 8, 9, T, J, Q, K, A).

Из-за этого меняется вероятность комбинаций, и порядок старшинства
подстраивают под реальность:

  • Флеш становится РЕДЧЕ фулл-хауса, поэтому флеш ставят ВЫШЕ.
  • Тройка становится РЕДЧЕ стрита, поэтому тройку ставят ВЫШЕ.

Ещё одно отличие: младший стрит — это A-6-7-8-9, туз в нём работает
как пятёрка (ведь двоек, троек, четвёрок и пятёрок в колоде нет).

Итоговый порядок от сильнейшего к слабейшему:
  стрит-флеш > каре > ФЛЕШ > фулл-хаус > ТРОЙКА > стрит >
  две пары > пара > старшая карта
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Iterable, List, Sequence, Tuple

from core.cards import Card, RANK_GENITIVE_RU, RANK_PLURAL_RU, short_deck
from core.variant import HIGH, Variant

# Свои номера категорий: порядок отличается от обычного покера.
SD_STRAIGHT_FLUSH = 8
SD_QUADS = 7
SD_FLUSH = 6
SD_FULL_HOUSE = 5
SD_TRIPS = 4
SD_STRAIGHT = 3
SD_TWO_PAIR = 2
SD_PAIR = 1
SD_HIGH_CARD = 0

SD_CATEGORY_NAMES = {
    SD_STRAIGHT_FLUSH: "Стрит-флеш",
    SD_QUADS: "Каре",
    SD_FLUSH: "Флеш",
    SD_FULL_HOUSE: "Фулл-хаус",
    SD_TRIPS: "Тройка",
    SD_STRAIGHT: "Стрит",
    SD_TWO_PAIR: "Две пары",
    SD_PAIR: "Пара",
    SD_HIGH_CARD: "Старшая карта",
}

SD_CATEGORY_SHAPES = {
    SD_STRAIGHT_FLUSH: "straight_flush",
    SD_QUADS: "quads",
    SD_FLUSH: "flush",
    SD_FULL_HOUSE: "full_house",
    SD_TRIPS: "trips",
    SD_STRAIGHT: "straight",
    SD_TWO_PAIR: "two_pair",
    SD_PAIR: "pair",
    SD_HIGH_CARD: "high_card",
}

# Порядок для показа в уроке: от сильнейшей комбинации к слабейшей.
SD_ORDER = [SD_STRAIGHT_FLUSH, SD_QUADS, SD_FLUSH, SD_FULL_HOUSE, SD_TRIPS,
            SD_STRAIGHT, SD_TWO_PAIR, SD_PAIR, SD_HIGH_CARD]


def _straight_high(ranks: Iterable[int]) -> int:
    """Старшая карта стрита в короткой колоде.

    Туз играет и старшим (T-J-Q-K-A), и как пятёрка (A-6-7-8-9) —
    иначе младшего стрита в этой колоде не существовало бы.
    """
    present = set(ranks)
    if 14 in present:
        present.add(5)
    for high in range(14, 8, -1):
        if all(high - offset in present for offset in range(5)):
            return high
    return 0


def evaluate(cards: Sequence[Card]) -> Tuple[int, ...]:
    """Оценка руки по правилам короткой колоды."""
    rank_counts = Counter(card.rank for card in cards)
    suit_counts = Counter(card.suit for card in cards)
    groups = sorted(rank_counts.items(), key=lambda item: (-item[1], -item[0]))
    ordered_ranks = sorted((card.rank for card in cards), reverse=True)

    def kickers(exclude: Sequence[int], how_many: int) -> Tuple[int, ...]:
        rest = [rank for rank in ordered_ranks if rank not in exclude]
        return tuple(rest[:how_many])

    top_rank, top_count = groups[0]

    # Каре проверяем до флеша: здесь каре всё ещё сильнее флеша.
    if top_count == 4:
        return (SD_QUADS, top_rank) + kickers([top_rank], 1)

    for suit, count in suit_counts.items():
        if count >= 5:
            flush_ranks = sorted(
                (card.rank for card in cards if card.suit == suit), reverse=True)
            high = _straight_high(flush_ranks)
            if high:
                return (SD_STRAIGHT_FLUSH, high)
            return (SD_FLUSH,) + tuple(flush_ranks[:5])

    if top_count == 3:
        pair_rank = next((rank for rank, count in groups[1:] if count >= 2), 0)
        if pair_rank:
            return (SD_FULL_HOUSE, top_rank, pair_rank)
        # Тройка сильнее стрита — отвечаем не дожидаясь проверки стрита.
        return (SD_TRIPS, top_rank) + kickers([top_rank], 2)

    high = _straight_high(ordered_ranks)
    if high:
        return (SD_STRAIGHT, high)

    if top_count == 2:
        pairs = [rank for rank, count in groups if count == 2]
        if len(pairs) >= 2:
            return (SD_TWO_PAIR, pairs[0], pairs[1]) + kickers(pairs[:2], 1)
        return (SD_PAIR, top_rank) + kickers([top_rank], 3)

    return (SD_HIGH_CARD,) + tuple(ordered_ranks[:5])


def best_five(cards: Sequence[Card]) -> List[Card]:
    if len(cards) <= 5:
        return list(cards)
    return list(max(combinations(cards, 5), key=evaluate))


def describe(cards: Sequence[Card]) -> str:
    score = evaluate(cards)
    category, name = score[0], SD_CATEGORY_NAMES[score[0]]
    if category == SD_STRAIGHT_FLUSH:
        if score[1] == 14:
            return "Флеш-рояль — сильнейшая рука"
        if score[1] == 9:
            return "%s A-6-7-8-9 (младший стрит короткой колоды)" % name
        return "%s до %s" % (name, RANK_GENITIVE_RU[score[1]])
    if category == SD_QUADS:
        return "%s %s" % (name, RANK_PLURAL_RU[score[1]])
    if category == SD_FLUSH:
        return "%s до %s (здесь флеш сильнее фулл-хауса)" % (
            name, RANK_GENITIVE_RU[score[1]])
    if category == SD_FULL_HOUSE:
        return "%s: три %s и пара %s" % (
            name, RANK_GENITIVE_RU[score[1]], RANK_PLURAL_RU[score[2]])
    if category == SD_TRIPS:
        return "%s: три %s (здесь тройка сильнее стрита)" % (
            name, RANK_GENITIVE_RU[score[1]])
    if category == SD_STRAIGHT:
        if score[1] == 9:
            return "%s A-6-7-8-9 (младший стрит короткой колоды)" % name
        return "%s до %s" % (name, RANK_GENITIVE_RU[score[1]])
    if category == SD_TWO_PAIR:
        return "%s: %s и %s" % (name, RANK_PLURAL_RU[score[1]],
                                RANK_PLURAL_RU[score[2]])
    if category == SD_PAIR:
        return "%s %s" % (name, RANK_PLURAL_RU[score[1]])
    return "%s — %s" % (name, RANK_GENITIVE_RU[score[1]])


def evaluate_high(hole: Sequence[Card], board: Sequence[Card]) -> Tuple:
    return evaluate(tuple(hole) + tuple(board))


def describe_high(hole: Sequence[Card], board: Sequence[Card]) -> str:
    cards = tuple(hole) + tuple(board)
    if len(cards) < 5:
        return "комбинации ещё нет — карт меньше пяти"
    return describe(cards)


VARIANT = Variant(
    key="short_deck",
    name="Шортдек-холдем",
    short_description="холдем на 36 картах, где флеш сильнее фулл-хауса, "
                      "а тройка сильнее стрита",
    hole_size=2,
    board_size=5,
    deck=short_deck,
    mode=HIGH,
    evaluate_high=evaluate_high,
    describe_high=describe_high,
    streets=("префлоп", "флоп", "тёрн", "ривер"),
    terms=("short_deck", "texas_holdem", "outs", "pot_odds"),
    category_names=SD_CATEGORY_NAMES,
    category_order=SD_ORDER,
    category_shapes=SD_CATEGORY_SHAPES,
    typical_players="2-9",
    default_iterations=25_000,
)
