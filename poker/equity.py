"""Расчёт equity — вашей доли в банке.

Equity = какую часть банка вы в среднем заберёте, если раздачу доиграют
до конца без дальнейших ставок. Если ваша equity 70%, а в банке 100,
то «справедливо» ваши — 70.

Считаем двумя способами:
  • точный перебор — когда неизвестных карт мало (все варианты борда);
  • Монте-Карло — когда вариантов слишком много: раздаём случайные
    карты много тысяч раз и смотрим, как часто рука выигрывает.
Второй способ приблизительный, но ошибка при 20-50 тысячах раздач
составляет доли процента — для обучения более чем достаточно.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import combinations
from math import comb
from typing import List, Optional, Sequence, Tuple

from .cards import Card, full_deck
from .evaluator import evaluate

# Выше этого числа вариантов точный перебор становится медленным —
# переключаемся на Монте-Карло.
EXACT_LIMIT = 200_000


@dataclass
class EquityResult:
    """Результат расчёта для героя и каждого из соперников."""
    hero_win: float          # доля раздач, где герой выиграл единолично
    hero_tie: float          # доля раздач, где герой разделил банк
    hero_equity: float       # итоговая доля банка (сплит делится по-честному)
    villain_equities: List[float] = field(default_factory=list)
    samples: int = 0
    exact: bool = False

    @property
    def hero_lose(self) -> float:
        return max(0.0, 1.0 - self.hero_win - self.hero_tie)

    def summary(self) -> str:
        method = "точный перебор" if self.exact else "Монте-Карло, %d раздач" % self.samples
        lines = [
            "Ваша equity: %.1f%%   (%s)" % (self.hero_equity * 100, method),
            "  выигрыш: %.1f%%   ничья: %.1f%%   проигрыш: %.1f%%"
            % (self.hero_win * 100, self.hero_tie * 100, self.hero_lose * 100),
        ]
        for index, value in enumerate(self.villain_equities, start=1):
            lines.append("  соперник %d: %.1f%%" % (index, value * 100))
        return "\n".join(lines)


def _showdown(hands: Sequence[Sequence[Card]], board: Sequence[Card]) -> List[int]:
    """Индексы победителей вскрытия (их может быть несколько при ничьей)."""
    best_score = None
    winners: List[int] = []
    for index, hand in enumerate(hands):
        score = evaluate(tuple(hand) + tuple(board))
        if best_score is None or score > best_score:
            best_score, winners = score, [index]
        elif score == best_score:
            winners.append(index)
    return winners


def equity(
    hero: Sequence[Card],
    villains: Sequence[Optional[Sequence[Card]]],
    board: Sequence[Card] = (),
    iterations: int = 20_000,
    seed: Optional[int] = None,
) -> EquityResult:
    """Equity героя против соперников.

    villains — список рук соперников; None означает «карты неизвестны»
    (тогда сопернику раздаются случайные карты, то есть считаем
    против «любой руки»).
    """
    if len(hero) != 2:
        raise ValueError("У героя должно быть ровно 2 карты.")
    if len(board) > 5:
        raise ValueError("На борде не может быть больше 5 карт.")
    if not villains:
        raise ValueError("Нужен хотя бы один соперник.")

    known: List[Card] = list(hero) + list(board)
    for villain in villains:
        if villain is not None:
            if len(villain) != 2:
                raise ValueError("У каждого соперника должно быть 2 карты.")
            known.extend(villain)
    if len(set(known)) != len(known):
        raise ValueError("Одна и та же карта использована дважды.")

    deck = [card for card in full_deck() if card not in set(known)]
    board_needed = 5 - len(board)
    unknown_villains = [i for i, villain in enumerate(villains) if villain is None]
    cards_needed = board_needed + 2 * len(unknown_villains)

    totals = [0.0] * (1 + len(villains))
    hero_win = hero_tie = 0
    played = 0

    def account(hands: Sequence[Sequence[Card]], full_board: Sequence[Card]) -> None:
        nonlocal hero_win, hero_tie
        winners = _showdown(hands, full_board)
        share = 1.0 / len(winners)
        for winner in winners:
            totals[winner] += share
        if 0 in winners:
            if len(winners) == 1:
                hero_win += 1
            else:
                hero_tie += 1

    # Точный перебор возможен, только если все руки известны —
    # тогда неизвестны лишь карты борда.
    variants = comb(len(deck), cards_needed) if cards_needed else 1
    use_exact = not unknown_villains and variants <= EXACT_LIMIT

    if use_exact:
        hands = [list(hero)] + [list(v) for v in villains]  # type: ignore[arg-type]
        for extra in combinations(deck, board_needed):
            account(hands, tuple(board) + extra)
            played += 1
    else:
        rng = random.Random(seed)
        for _ in range(iterations):
            drawn = rng.sample(deck, cards_needed)
            cursor = board_needed
            hands = [list(hero)]
            for villain in villains:
                if villain is None:
                    hands.append(drawn[cursor:cursor + 2])
                    cursor += 2
                else:
                    hands.append(list(villain))
            account(hands, tuple(board) + tuple(drawn[:board_needed]))
            played += 1

    return EquityResult(
        hero_win=hero_win / played,
        hero_tie=hero_tie / played,
        hero_equity=totals[0] / played,
        villain_equities=[total / played for total in totals[1:]],
        samples=played,
        exact=use_exact,
    )


def equity_vs_random(
    hero: Sequence[Card],
    opponents: int = 1,
    iterations: int = 20_000,
    seed: Optional[int] = None,
) -> EquityResult:
    """Equity руки против заданного числа соперников со случайными картами."""
    return equity(hero, [None] * opponents, (), iterations=iterations, seed=seed)


def outs_vs_villain(
    hero: Sequence[Card],
    villain: Sequence[Card],
    board: Sequence[Card],
) -> Tuple[List[Card], List[Card]]:
    """Аутсы: карты, которые превращают проигрыш в выигрыш.

    Возвращает (аутсы, карты-ничьи): какие карты следующей улицы делают
    руку героя сильнее руки соперника, а какие уравнивают их.
    Имеет смысл, когда на борде 3 или 4 карты.
    """
    if not 3 <= len(board) <= 4:
        raise ValueError("Аутсы считают на флопе (3 карты) или на тёрне (4 карты).")

    used = set(hero) | set(villain) | set(board)
    deck = [card for card in full_deck() if card not in used]

    outs: List[Card] = []
    ties: List[Card] = []
    for card in deck:
        new_board = tuple(board) + (card,)
        hero_score = evaluate(tuple(hero) + new_board)
        villain_score = evaluate(tuple(villain) + new_board)
        if hero_score > villain_score:
            outs.append(card)
        elif hero_score == villain_score:
            ties.append(card)
    return outs, ties


def improving_cards(hero: Sequence[Card], board: Sequence[Card]) -> List[Card]:
    """Карты, которые усиливают саму комбинацию героя (без оглядки на соперника)."""
    used = set(hero) | set(board)
    deck = [card for card in full_deck() if card not in used]
    current = evaluate(tuple(hero) + tuple(board))
    return [
        card for card in deck
        if evaluate(tuple(hero) + tuple(board) + (card,))[0] > current[0]
    ]


def rule_of_2_and_4(outs: int, cards_to_come: int) -> float:
    """«Правило 2 и 4» — оценка шанса попасть в аутс в уме.

    Одна карта впереди (тёрн→ривер): аутсы × 2 процента.
    Две карты впереди (флоп→ривер): аутсы × 4 процента.
    """
    multiplier = 4 if cards_to_come >= 2 else 2
    return min(1.0, outs * multiplier / 100.0)


def exact_improve_chance(outs: int, unseen: int, cards_to_come: int) -> float:
    """Точная вероятность попасть хотя бы в один аутс."""
    miss = unseen - outs
    probability_miss = 1.0
    for step in range(cards_to_come):
        probability_miss *= (miss - step) / (unseen - step)
    return 1.0 - probability_miss


def required_equity(pot: float, call: float) -> float:
    """Пот-оддсы: какая equity нужна, чтобы колл был безубыточным.

    Вы вкладываете `call`, чтобы сыграть за банк размером `pot + call`.
    Значит, выигрывать нужно не реже, чем call / (pot + call).
    """
    if call <= 0:
        raise ValueError("Размер колла должен быть больше нуля.")
    return call / (pot + call)
