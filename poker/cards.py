"""Карты: обозначения, парсинг, красивый вывод.

Карта записывается двумя символами: номинал + масть.
  Номиналы: 2 3 4 5 6 7 8 9 T J Q K A   (T = 10, J = валет, Q = дама, K = король, A = туз)
  Масти:    s = пики ♠, h = червы ♥, d = бубны ♦, c = трефы ♣

Примеры: "As" = туз пик, "Th" = десятка червей, "7d" = семёрка бубен.
"""
from __future__ import annotations

from typing import Iterable, List, NamedTuple

RANK_CHARS = "23456789TJQKA"
SUIT_CHARS = "shdc"

RANK_VALUES = {ch: value for value, ch in enumerate(RANK_CHARS, start=2)}
VALUE_CHARS = {value: ch for ch, value in RANK_VALUES.items()}

SUIT_SYMBOLS = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}
SUIT_NAMES_RU = {"s": "пики", "h": "червы", "d": "бубны", "c": "трефы"}
RED_SUITS = ("h", "d")

RANK_NAMES_RU = {
    2: "двойка", 3: "тройка", 4: "четвёрка", 5: "пятёрка", 6: "шестёрка",
    7: "семёрка", 8: "восьмёрка", 9: "девятка", 10: "десятка",
    11: "валет", 12: "дама", 13: "король", 14: "туз",
}
# Родительный падеж единственного числа — для фраз «флеш до туза», «три туза».
RANK_GENITIVE_RU = {
    2: "двойки", 3: "тройки", 4: "четвёрки", 5: "пятёрки", 6: "шестёрки",
    7: "семёрки", 8: "восьмёрки", 9: "девятки", 10: "десятки",
    11: "валета", 12: "дамы", 13: "короля", 14: "туза",
}
# Родительный падеж множественного числа — для фраз «пара королей», «каре тузов».
RANK_PLURAL_RU = {
    2: "двоек", 3: "троек", 4: "четвёрок", 5: "пятёрок", 6: "шестёрок",
    7: "семёрок", 8: "восьмёрок", 9: "девяток", 10: "десяток",
    11: "валетов", 12: "дам", 13: "королей", 14: "тузов",
}

# Пользователь может писать масть и по-русски, и символом — принимаем всё.
SUIT_ALIASES = {
    "s": "s", "♠": "s", "п": "s", "p": "s",
    "h": "h", "♥": "h", "ч": "h",
    "d": "d", "♦": "d", "б": "d",
    "c": "c", "♣": "c", "к": "c", "t": "c",
}


class BadCard(ValueError):
    """Пользователь ввёл что-то, что не похоже на карту."""


class Card(NamedTuple):
    rank: int   # 2..14
    suit: str   # "s" / "h" / "d" / "c"

    def __str__(self) -> str:
        return VALUE_CHARS[self.rank] + self.suit

    @property
    def pretty(self) -> str:
        """Карта с символом масти и цветом для терминала."""
        text = VALUE_CHARS[self.rank] + SUIT_SYMBOLS[self.suit]
        if self.suit in RED_SUITS:
            return "\033[31m" + text + "\033[0m"
        return "\033[1m" + text + "\033[0m"

    @property
    def name_ru(self) -> str:
        return RANK_NAMES_RU[self.rank] + " " + SUIT_NAMES_RU[self.suit]


def full_deck() -> List[Card]:
    """Полная колода из 52 карт."""
    return [Card(RANK_VALUES[r], s) for r in RANK_CHARS for s in SUIT_CHARS]


def parse_card(text: str) -> Card:
    text = text.strip()
    if text.lower().startswith("10"):          # "10h" пишут чаще, чем "Th"
        text = "T" + text[2:]
    if len(text) != 2:
        raise BadCard("«%s» — не похоже на карту. Пример: As, Th, 7d." % text)
    rank_char, suit_char = text[0].upper(), text[1].lower()
    if rank_char not in RANK_VALUES:
        raise BadCard("Непонятный номинал «%s». Номиналы: 2-9, T, J, Q, K, A." % text[0])
    if suit_char not in SUIT_ALIASES:
        raise BadCard("Непонятная масть «%s». Масти: s ♠, h ♥, d ♦, c ♣." % text[1])
    return Card(RANK_VALUES[rank_char], SUIT_ALIASES[suit_char])


def _split_chunk(chunk: str) -> List[str]:
    """Режет склеенную запись «AsKhQd» на отдельные карты.

    Карта — всегда два символа, кроме записи десятки как «10».
    """
    tokens: List[str] = []
    position = 0
    while position < len(chunk):
        width = 3 if chunk[position:position + 2] == "10" else 2
        tokens.append(chunk[position:position + width])
        position += width
    return tokens


def parse_cards(text: str) -> List[Card]:
    """Разбирает строку в список карт.

    Понимает и «AsKh», и «As Kh», и «As, Kh», и «10h Jh».
    Заодно проверяет, что одна и та же карта не названа дважды.
    """
    cleaned = text.replace(",", " ").strip()
    if not cleaned:
        return []

    tokens: List[str] = []
    for chunk in cleaned.split():
        tokens.extend(_split_chunk(chunk))

    cards = [parse_card(token) for token in tokens]
    seen = set()
    for card in cards:
        if card in seen:
            raise BadCard("Карта %s названа дважды — в колоде она одна." % (card,))
        seen.add(card)
    return cards


def check_no_duplicates(*groups: Iterable[Card]) -> None:
    """Убеждается, что одна карта не попала сразу в две руки или на борд."""
    seen = set()
    for group in groups:
        for card in group:
            if card in seen:
                raise BadCard("Карта %s использована дважды." % (card,))
            seen.add(card)


def pretty(cards: Iterable[Card]) -> str:
    return " ".join(card.pretty for card in cards) or "—"


def plain(cards: Iterable[Card]) -> str:
    return "".join(str(card) for card in cards)
