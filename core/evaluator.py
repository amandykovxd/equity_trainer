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

# От сильнейшей комбинации к слабейшей — для квизов и уроков.
CATEGORY_ORDER = [STRAIGHT_FLUSH, FOUR_OF_A_KIND, FULL_HOUSE, FLUSH, STRAIGHT,
                  THREE_OF_A_KIND, TWO_PAIR, ONE_PAIR, HIGH_CARD]

# Форма комбинации независимо от нумерации: в шортдеке номера другие,
# а формы те же.
CATEGORY_SHAPES = {
    STRAIGHT_FLUSH: "straight_flush",
    FOUR_OF_A_KIND: "quads",
    FULL_HOUSE: "full_house",
    FLUSH: "flush",
    STRAIGHT: "straight",
    THREE_OF_A_KIND: "trips",
    TWO_PAIR: "two_pair",
    ONE_PAIR: "pair",
    HIGH_CARD: "high_card",
}

Score = Tuple[int, ...]


# Поиск стрита вызывается миллионы раз за один расчёт equity, поэтому
# результат кэшируется по битовой маске достоинств: одни и те же наборы
# повторяются постоянно.
_STRAIGHT_CACHE = {}


def _straight_high(ranks: Iterable[int], wheel: bool = True) -> int:
    """Старшая карта стрита или 0, если стрита нет.

    Туз умеет быть и старшим, и младшим: A-2-3-4-5 — это тоже стрит
    (его называют «колесо»), и в нём туз считается за единицу.
    В игре 2-7 туз всегда старший, поэтому там wheel=False.
    """
    mask = 0
    for rank in ranks:
        mask |= 1 << rank
    if wheel and mask & (1 << 14):
        mask |= 1 << 1
    cached = _STRAIGHT_CACHE.get(mask)
    if cached is not None:
        return cached
    result = 0
    for high in range(14, 4, -1):
        # Пять подряд идущих бит, начиная с high - 4.
        if (mask >> (high - 4)) & 0b11111 == 0b11111:
            result = high
            break
    _STRAIGHT_CACHE[mask] = result
    return result


def evaluate(cards: Sequence[Card], wheel: bool = True) -> Score:
    """Оценка лучшей пятикарточной комбинации из переданных карт.

    wheel=False отключает стрит A-2-3-4-5 — он не существует в играх,
    где туз всегда старший (например, в лоуболе 2-7).

    Функция вызывается миллионы раз за один расчёт equity, поэтому
    написана подчёркнуто прямолинейно: ручной подсчёт вместо Counter
    и никаких сортировок до того момента, когда они действительно нужны.
    """
    rank_counts = {}
    suit_counts = {}
    for card in cards:
        rank = card.rank
        suit = card.suit
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
        suit_counts[suit] = suit_counts.get(suit, 0) + 1

    # --- Флеш и стрит-флеш ---
    # Если пять карт одной масти есть, то каре и фулл-хаус уже невозможны
    # (на них просто не хватит карт), поэтому можно отвечать сразу.
    for suit, count in suit_counts.items():
        if count >= 5:
            flush_ranks = sorted(
                (card.rank for card in cards if card.suit == suit), reverse=True)
            high = _straight_high(flush_ranks, wheel)
            if high:
                return (STRAIGHT_FLUSH, high)
            return (FLUSH,) + tuple(flush_ranks[:5])

    # Достоинства, сгруппированные по количеству одинаковых карт.
    by_count = {}
    for rank, count in rank_counts.items():
        if count in by_count:
            by_count[count].append(rank)
        else:
            by_count[count] = [rank]

    ordered_ranks = sorted(rank_counts, reverse=True)
    full_ranks = []
    for rank in ordered_ranks:
        full_ranks.extend([rank] * rank_counts[rank])

    def kickers(exclude, how_many: int) -> Tuple[int, ...]:
        rest = [rank for rank in full_ranks if rank not in exclude]
        return tuple(rest[:how_many])

    quads = by_count.get(4)
    if quads:
        top = max(quads)
        return (FOUR_OF_A_KIND, top) + kickers((top,), 1)

    trips = by_count.get(3)
    pairs = by_count.get(2)
    if trips:
        top_trips = max(trips)
        if pairs or len(trips) > 1:
            # Пара для фулл-хауса может прийти и из второй тройки.
            candidates = list(pairs or [])
            candidates += [rank for rank in trips if rank != top_trips]
            return (FULL_HOUSE, top_trips, max(candidates))

    straight_high = _straight_high(ordered_ranks, wheel)
    if straight_high:
        return (STRAIGHT, straight_high)

    if trips:
        top_trips = max(trips)
        return (THREE_OF_A_KIND, top_trips) + kickers((top_trips,), 2)

    if pairs:
        if len(pairs) >= 2:
            ranked = sorted(pairs, reverse=True)
            high_pair, low_pair = ranked[0], ranked[1]
            return (TWO_PAIR, high_pair, low_pair) + kickers(
                (high_pair, low_pair), 1)
        return (ONE_PAIR, pairs[0]) + kickers((pairs[0],), 3)

    return (HIGH_CARD,) + tuple(full_ranks[:5])


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
