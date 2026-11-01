"""Описание разновидности покера.

Все разновидности различаются одним и тем же набором параметров:
сколько карт на руках, есть ли общие карты, какая колода, и побеждает
сильнейшая комбинация или слабейшая. Один раз описав это, можно считать
equity для любой игры одним и тем же движком.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .cards import Card

# Оценка руки: берёт карманные карты и борд, возвращает кортеж для сравнения.
Evaluator = Callable[[Sequence[Card], Sequence[Card]], Optional[Tuple]]
Describer = Callable[[Sequence[Card], Sequence[Card]], str]

# Как определяется победитель:
HIGH = "high"    # побеждает сильнейшая комбинация (холдем, омаха, стад)
LOW = "low"      # побеждает слабейшая комбинация (разз, 2-7, бадуги)
SPLIT = "split"  # банк делится между сильнейшей и слабейшей (хай-лоу)


@dataclass
class Variant:
    """Правила одной разновидности покера."""

    key: str                 # имя папки, например "texas_holdem"
    name: str                # название по-русски
    short_description: str   # одна строка: чем эта игра отличается
    hole_size: int           # сколько карт на руках у игрока
    board_size: int          # сколько общих карт (0 — общих нет)
    deck: Callable[[], List[Card]]
    mode: str = HIGH
    evaluate_high: Optional[Evaluator] = None
    evaluate_low: Optional[Evaluator] = None
    describe_high: Optional[Describer] = None
    describe_low: Optional[Describer] = None
    # Названия кругов ставок — у разных игр они свои.
    streets: Sequence[str] = ()
    # Ключи терминов из словаря, важные именно для этой игры.
    terms: Sequence[str] = ()
    # Для квиза «назови комбинацию»: названия категорий и их порядок
    # от сильнейшей к слабейшей. Есть только у игр на старшую руку.
    category_names: Optional[Dict[int, str]] = None
    category_order: Sequence[int] = ()
    # Форма комбинации по её номеру — нужна генератору рук для квизов.
    category_shapes: Optional[Dict[int, str]] = None
    # Есть ли в игре ситуация «осталась одна известная карта» — на ней
    # строится тренажёр «колл или фолд». В дро-играх такой ситуации нет:
    # там карты меняют, а не добирают.
    supports_next_card_drill: bool = True
    # Сколько соперников осмысленно за столом.
    typical_players: str = "2-9"
    # Сколько раздач крутить в Монте-Карло по умолчанию. Там, где оценка
    # одной руки дорогая (омаха перебирает 60 комбинаций), число меньше.
    default_iterations: int = 20_000

    def board_stage(self, board_length: int) -> str:
        """Как называется текущая улица при таком числе общих карт."""
        if not self.board_size:
            return ""
        names = {0: "префлоп", 3: "флоп", 4: "тёрн", 5: "ривер"}
        return names.get(board_length, "%d общих карт" % board_length)

    def describe(self, hole: Sequence[Card], board: Sequence[Card] = ()) -> str:
        """Человеческое описание руки с учётом режима игры."""
        parts: List[str] = []
        if self.describe_high and self.mode in (HIGH, SPLIT):
            parts.append(self.describe_high(hole, board))
        if self.describe_low and self.mode in (LOW, SPLIT):
            low = self.describe_low(hole, board)
            parts.append(low)
        return "   |   ".join(part for part in parts if part)
