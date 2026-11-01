"""Универсальный расчёт equity — один движок для всех разновидностей покера.

Equity — это доля банка, которая «ваша по справедливости». Если ваша
equity 70%, то при многократном повторении этой ситуации вы забирали бы
70% банка.

Движок не знает, во что именно вы играете: правила приходят к нему
объектом Variant (см. variant.py). Поэтому один и тот же код считает
и холдем, и разз, и бадуги.

Считаем двумя способами:
  • точный перебор — когда неизвестных карт мало (все варианты борда);
  • Монте-Карло — когда вариантов слишком много: раздаём случайные
    карты много тысяч раз и смотрим, как часто рука выигрывает.
Второй способ приблизительный, но при 20 000 раздач ошибка составляет
доли процента — для обучения более чем достаточно.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import combinations
from math import comb
from typing import List, Optional, Sequence, Tuple

from .cards import Card
from .variant import HIGH, LOW, SPLIT, Variant

# Выше этого числа вариантов точный перебор становится медленным —
# переключаемся на Монте-Карло.
EXACT_LIMIT = 150_000

Hand = Sequence[Card]


@dataclass
class EquityResult:
    """Результат расчёта для героя и каждого из соперников."""

    hero_win: float               # доля раздач, где герой забрал весь банк
    hero_tie: float               # доля раздач, где банк разделили
    hero_equity: float            # итоговая доля банка
    villain_equities: List[float] = field(default_factory=list)
    samples: int = 0
    exact: bool = False
    # Только для игр с разделением банка (хай-лоу):
    hero_high_share: float = 0.0  # доля от хай-половины
    hero_low_share: float = 0.0   # доля от лоу-половины
    hero_scoops: float = 0.0      # доля раздач, где герой забрал обе половины
    no_low: float = 0.0           # доля раздач, где лоу ни у кого не собралось

    @property
    def hero_lose(self) -> float:
        return max(0.0, 1.0 - self.hero_win - self.hero_tie)

    def summary(self, variant: Optional[Variant] = None) -> str:
        method = ("точный перебор" if self.exact
                  else "Монте-Карло, %d раздач" % self.samples)
        lines = [
            "Ваша equity: %.1f%%   (%s)" % (self.hero_equity * 100, method),
            "  весь банк: %.1f%%   часть банка: %.1f%%   ничего: %.1f%%"
            % (self.hero_win * 100, self.hero_tie * 100, self.hero_lose * 100),
        ]
        if variant is not None and variant.mode == SPLIT:
            lines.append("  хай-половина: %.1f%%   лоу-половина: %.1f%%"
                         % (self.hero_high_share * 100, self.hero_low_share * 100))
            lines.append("  забрали весь банк («скуп»): %.1f%%   "
                         "лоу ни у кого: %.1f%%"
                         % (self.hero_scoops * 100, self.no_low * 100))
        for index, value in enumerate(self.villain_equities, start=1):
            lines.append("  соперник %d: %.1f%%" % (index, value * 100))
        return "\n".join(lines)


def pot_shares(
    variant: Variant,
    hands: Sequence[Hand],
    board: Hand = (),
) -> Tuple[List[float], bool]:
    """Как делится банк между руками. Возвращает (доли, было_ли_лоу).

    Доли в сумме дают 1. При ничьей доля делится поровну.
    """
    shares = [0.0] * len(hands)

    high_winners: List[int] = []
    if variant.mode in (HIGH, SPLIT):
        scores = [variant.evaluate_high(hand, board) for hand in hands]
        best = max(scores)
        high_winners = [i for i, score in enumerate(scores) if score == best]

    low_winners: List[int] = []
    if variant.mode in (LOW, SPLIT):
        low_scores = [variant.evaluate_low(hand, board) for hand in hands]
        qualified = [(i, score) for i, score in enumerate(low_scores)
                     if score is not None]
        if qualified:
            best_low = min(score for _index, score in qualified)
            low_winners = [i for i, score in qualified if score == best_low]

    if variant.mode == HIGH:
        for index in high_winners:
            shares[index] += 1.0 / len(high_winners)
        return shares, False

    if variant.mode == LOW:
        # В чистых лоу-играх рука есть всегда, так что победитель найдётся.
        for index in low_winners:
            shares[index] += 1.0 / len(low_winners)
        return shares, bool(low_winners)

    # Хай-лоу: половина банка сильнейшей руке, половина слабейшей.
    # Если лоу ни у кого не собралось, хай забирает всё.
    if not low_winners:
        for index in high_winners:
            shares[index] += 1.0 / len(high_winners)
        return shares, False
    for index in high_winners:
        shares[index] += 0.5 / len(high_winners)
    for index in low_winners:
        shares[index] += 0.5 / len(low_winners)
    return shares, True


def _validate(variant: Variant, players: Sequence[Hand], board: Hand) -> None:
    if len(players) < 2:
        raise ValueError("Нужны как минимум вы и один соперник.")
    for index, hand in enumerate(players):
        if len(hand) > variant.hole_size:
            raise ValueError(
                "В %s у игрока не бывает больше %d карт, у игрока %d их %d."
                % (variant.name, variant.hole_size, index + 1, len(hand)))
    if len(board) > variant.board_size:
        raise ValueError(
            "В %s на борде не бывает больше %d карт."
            % (variant.name, variant.board_size))
    known = [card for hand in players for card in hand] + list(board)
    if len(set(known)) != len(known):
        raise ValueError("Одна и та же карта использована дважды.")
    deck_size = len(variant.deck())
    if len(known) > deck_size:
        raise ValueError("Карт больше, чем есть в колоде (%d)." % deck_size)
    for card in known:
        if card not in set(variant.deck()):
            raise ValueError(
                "Карты %s нет в колоде этой игры (%s)." % (card, variant.name))


def equity(
    variant: Variant,
    players: Sequence[Hand],
    board: Hand = (),
    iterations: Optional[int] = None,
    seed: Optional[int] = None,
) -> EquityResult:
    """Equity каждого игрока. players[0] — это вы.

    У любого игрока можно указать не все карты: недостающие будут
    раздаваться случайно. Пустой список означает «карты неизвестны».
    """
    _validate(variant, players, board)
    iterations = iterations or variant.default_iterations

    known = {card for hand in players for card in hand} | set(board)
    deck = [card for card in variant.deck() if card not in known]
    board_needed = variant.board_size - len(board)
    hole_needed = [variant.hole_size - len(hand) for hand in players]
    cards_needed = board_needed + sum(hole_needed)
    if cards_needed > len(deck):
        raise ValueError("В колоде не хватает карт на такую раздачу.")

    totals = [0.0] * len(players)
    hero_win = hero_tie = 0
    high_total = low_total = scoops = 0.0
    low_happened = 0
    played = 0

    def account(hands: Sequence[Hand], full_board: Hand) -> None:
        nonlocal hero_win, hero_tie, high_total, low_total, scoops, low_happened
        shares, had_low = pot_shares(variant, hands, full_board)
        for index, share in enumerate(shares):
            totals[index] += share
        hero_share = shares[0]
        if hero_share >= 1.0:
            hero_win += 1
        elif hero_share > 0.0:
            hero_tie += 1
        if variant.mode == SPLIT:
            # Доли героя в каждой половине банка считаем всегда одинаково,
            # иначе числа в отчёте означают разное в разных раздачах.
            high_part, low_part = _split_detail(variant, hands, full_board)
            high_total += high_part
            low_total += low_part
            if had_low:
                low_happened += 1
                scooped = high_part >= 1.0 and low_part >= 1.0
            else:
                scooped = high_part >= 1.0
            if scooped:
                scoops += 1

    # Точный перебор возможен, только если у всех игроков известны все
    # карты — тогда неизвестен лишь борд.
    exact_possible = not any(hole_needed)
    variants_count = comb(len(deck), board_needed) if board_needed else 1
    use_exact = exact_possible and variants_count <= EXACT_LIMIT

    if use_exact:
        hands = [list(hand) for hand in players]
        if board_needed:
            for extra in combinations(deck, board_needed):
                account(hands, tuple(board) + extra)
                played += 1
        else:
            account(hands, tuple(board))
            played = 1
    else:
        rng = random.Random(seed)
        for _ in range(iterations):
            drawn = rng.sample(deck, cards_needed)
            cursor = board_needed
            hands = []
            for hand, needed in zip(players, hole_needed):
                if needed:
                    hands.append(list(hand) + drawn[cursor:cursor + needed])
                    cursor += needed
                else:
                    hands.append(list(hand))
            account(hands, tuple(board) + tuple(drawn[:board_needed]))
            played += 1

    return EquityResult(
        hero_win=hero_win / played,
        hero_tie=hero_tie / played,
        hero_equity=totals[0] / played,
        villain_equities=[total / played for total in totals[1:]],
        samples=played,
        exact=use_exact,
        hero_high_share=high_total / played,
        hero_low_share=low_total / played,
        hero_scoops=scoops / played,
        no_low=1.0 - low_happened / played,
    )


def _split_detail(
    variant: Variant,
    hands: Sequence[Hand],
    board: Hand,
) -> Tuple[float, float]:
    """Доли героя отдельно в хай- и лоу-половине банка."""
    high_scores = [variant.evaluate_high(hand, board) for hand in hands]
    best_high = max(high_scores)
    high_winners = [i for i, score in enumerate(high_scores) if score == best_high]
    high_part = (1.0 / len(high_winners)) if 0 in high_winners else 0.0

    low_scores = [variant.evaluate_low(hand, board) for hand in hands]
    qualified = [(i, score) for i, score in enumerate(low_scores) if score is not None]
    if not qualified:
        return high_part, 0.0
    best_low = min(score for _index, score in qualified)
    low_winners = [i for i, score in qualified if score == best_low]
    low_part = (1.0 / len(low_winners)) if 0 in low_winners else 0.0
    return high_part, low_part


# --------------------------------------------------------------------------
# Аутсы и пот-оддсы
# --------------------------------------------------------------------------

def next_card_outs(
    variant: Variant,
    hero: Hand,
    villain: Hand,
    board: Hand = (),
) -> Tuple[List[Card], List[Card]]:
    """Аутсы: карты, которые выводят героя вперёд. Возвращает (аутсы, ничьи).

    В играх с общими картами следующая карта кладётся на борд.
    В играх без общих карт (стад, дро) — добавляется в руку героя.
    """
    used = set(hero) | set(villain) | set(board)
    deck = [card for card in variant.deck() if card not in used]
    to_board = variant.board_size > 0

    outs: List[Card] = []
    ties: List[Card] = []
    for card in deck:
        if to_board:
            hands, new_board = [hero, villain], tuple(board) + (card,)
        else:
            hands, new_board = [tuple(hero) + (card,), villain], board
        shares, _had_low = pot_shares(variant, hands, new_board)
        if shares[0] > 0.5:
            outs.append(card)
        elif shares[0] == 0.5:
            ties.append(card)
    return outs, ties


def rule_of_2_and_4(outs: int, cards_to_come: int) -> float:
    """«Правило 2 и 4» — оценка шанса попасть в аут в уме.

    Одна карта впереди: аутсы × 2 процента.
    Две карты впереди: аутсы × 4 процента.
    """
    multiplier = 4 if cards_to_come >= 2 else 2
    return min(1.0, outs * multiplier / 100.0)


def exact_improve_chance(outs: int, unseen: int, cards_to_come: int) -> float:
    """Точная вероятность попасть хотя бы в один аут."""
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
