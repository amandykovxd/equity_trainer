#!/usr/bin/env python3
"""Самопроверка: сверяет расчёты с известными покерными значениями.

Если этот файл проходит, значит калькулятору можно доверять.
Запуск: python3 selftest.py   (или python3 trainer.py test)
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from poker.cards import BadCard, parse_cards as cards
from poker.cards import plain
from poker.equity import (
    equity,
    equity_vs_random,
    exact_improve_chance,
    outs_vs_villain,
    required_equity,
    rule_of_2_and_4,
)
from poker.evaluator import compare, describe, evaluate
from poker.ranges import hand_notation

_failures = []
_checks = 0


def check(condition: bool, label: str) -> None:
    global _checks
    _checks += 1
    if not condition:
        _failures.append(label)
        print("  \033[31mFAIL\033[0m  %s" % label)


def check_close(actual: float, expected: float, tolerance: float, label: str) -> None:
    ok = abs(actual - expected) <= tolerance
    check(ok, "%s: получено %.2f%%, ожидалось %.2f%% (±%.2f)"
          % (label, actual * 100, expected * 100, tolerance * 100))


def test_ranking_order() -> None:
    """Комбинации должны строго убывать по силе."""
    ladder = [
        "AsKsQsJsTs",  # стрит-флеш
        "7h7d7s7cKh",  # каре
        "AhAdAcKsKh",  # фулл-хаус
        "Ah9h7h4h2h",  # флеш
        "9s8d7h6c5s",  # стрит
        "QhQdQc8s3h",  # сет
        "AsAhKdKc7h",  # две пары
        "AsAhKdQc7h",  # пара
        "AsKdQh9c4s",  # старшая карта
    ]
    for stronger, weaker in zip(ladder, ladder[1:]):
        check(compare(cards(stronger), cards(weaker)) == 1,
              "%s должна быть сильнее %s" % (stronger, weaker))


def test_tiebreakers() -> None:
    check(compare(cards("AsAhKdQc7h"), cards("AsAhKdJc7h")) == 1,
          "кикер король должен бить кикер валет")
    check(compare(cards("AsAhKdQc7h"), cards("AcAdKsQh7d")) == 0,
          "одинаковые по силе руки — ничья")
    check(compare(cards("AsKsQsJs9s"), cards("KdQdJdTd8d")) == 1,
          "флеш до туза должен бить флеш до короля")
    check(compare(cards("AhAdAcKsKh"), cards("KdKcKhAsAd")) == 1,
          "фулл-хаус на тузах должен бить фулл-хаус на королях")
    check(compare(cards("2s2h2d3c3h"), cards("AsAhKdKc7h")) == 1,
          "самый младший фулл-хаус должен бить любые две пары")


def test_wheel() -> None:
    check(evaluate(cards("Ah5d4c3s2h"))[0] == 4, "A-2-3-4-5 — это стрит")
    check(compare(cards("6s5d4c3s2h"), cards("Ah5d4c3s2h")) == 1,
          "стрит до шестёрки должен бить колесо")
    check(evaluate(cards("Ah5h4h3h2h"))[0] == 8, "A-2-3-4-5 одной масти — стрит-флеш")


def test_seven_cards() -> None:
    """Из 7 карт должна выбираться лучшая пятёрка."""
    hand = cards("Ah2c") + cards("AsAd3h4s5c")
    check(evaluate(hand)[0] == 4,
          "стрит A-2-3-4-5 сильнее сета тузов: %s" % describe(hand))
    hand = cards("KhKd") + cards("KsAhAd2c3s")
    check(evaluate(hand)[0] == 6, "должен собраться фулл-хаус")
    royal = cards("AhKh") + cards("QhJhTh3d4s")
    check(evaluate(royal)[0] == 8, "должен найтись флеш-рояль")
    just_flush = cards("AhKh") + cards("QhJh2h3d4s")
    check(evaluate(just_flush)[0] == 5,
          "A-K-Q-J-2 одной масти — это флеш, а не стрит-флеш")


def test_known_equities() -> None:
    """Сверка с эталонными значениями.

    Первые четыре числа получены полным перебором всех возможных бордов
    (1 712 304 и 1 370 754 варианта) и совпадают с таблицами equity,
    которые публикуются в покерной литературе. Здесь они проверяются
    быстрым Монте-Карло, поэтому допуск — полтора процентных пункта.
    """
    check_close(equity(cards("AsAh"), [cards("KsKd")], seed=1).hero_equity,
                0.8195, 0.015, "AA против KK")
    check_close(equity(cards("AhKh"), [cards("2c2d")], seed=2).hero_equity,
                0.5008, 0.015, "AKs против 22")
    check_close(equity(cards("AsKd"), [cards("QsQd")], seed=3).hero_equity,
                0.4365, 0.015, "AKo против QQ")
    check_close(equity(cards("AsAh"), [cards("KsKd"), cards("QsQd")],
                       seed=6).hero_equity,
                0.6745, 0.020, "AA против KK и QQ")
    check_close(equity_vs_random(cards("AsAh"), 1, seed=4).hero_equity,
                0.852, 0.015, "AA против случайной руки")
    check_close(equity_vs_random(cards("7s2d"), 1, seed=5).hero_equity,
                0.346, 0.020, "72o против случайной руки")


def test_split_pot() -> None:
    """Одинаковые по силе руки должны делить банк ровно пополам."""
    result = equity(cards("AhKh"), [cards("AsKs")], cards("2d7c9hTs4c"))
    check_close(result.hero_equity, 0.5, 0.001, "одинаковые руки делят банк")
    check(result.exact, "при полном борде должен использоваться точный перебор")
    check_close(result.hero_tie, 1.0, 0.001, "это должна быть ничья в 100% случаев")


def test_exact_matches_monte_carlo() -> None:
    """Точный перебор и Монте-Карло должны давать близкие ответы."""
    hero, villain, board = cards("9h8h"), cards("KsQd"), cards("Kh7h2cAd")
    exact = equity(hero, [villain], board)
    check(exact.exact, "на тёрне перебор должен быть точным")
    monte = equity(hero, [villain], board, iterations=20000, seed=9)
    check_close(monte.hero_equity, exact.hero_equity, 0.02,
                "Монте-Карло близко к точному значению")


def test_outs() -> None:
    """Флеш-дро на флопе — это ровно 9 аутсов."""
    hero, villain, board = cards("9h8h"), cards("KsQd"), cards("Kh7h2c")
    outs, _ties = outs_vs_villain(hero, villain, board)
    check(len(outs) == 9, "у флеш-дро должно быть 9 аутсов, найдено %d" % len(outs))
    check(all(card.suit == "h" for card in outs), "все аутсы должны быть червами")

    # Открытый стрит-дро: 8 аутсов (четыре шестёрки и четыре валета).
    hero, villain, board = cards("9s8d"), cards("AhAc"), cards("7h Tc 2s")
    outs, _ties = outs_vs_villain(hero, villain, board)
    check(len(outs) == 8, "у открытого стрит-дро 8 аутсов, найдено %d" % len(outs))


def test_odds_math() -> None:
    check_close(required_equity(100, 50), 1 / 3, 0.001, "ставка в половину банка")
    check_close(required_equity(100, 100), 0.5, 0.001, "ставка в банк")
    check_close(rule_of_2_and_4(9, 2), 0.36, 0.001, "правило 4 для 9 аутсов")
    check_close(rule_of_2_and_4(9, 1), 0.18, 0.001, "правило 2 для 9 аутсов")
    check_close(exact_improve_chance(9, 47, 2), 0.350, 0.005,
                "точный шанс добрать флеш с флопа")
    check_close(exact_improve_chance(9, 46, 1), 0.196, 0.005,
                "точный шанс добрать флеш на ривере")


def test_parsing() -> None:
    """Карты должны разбираться в любом разумном написании."""
    check(plain(cards("AhKh")) == "AhKh", "слитная запись")
    check(plain(cards("As Kh")) == "AsKh", "запись через пробел")
    check(plain(cards("As, Kh, 10d")) == "AsKhTd", "запятые и «10» вместо T")
    check(plain(cards("AsKsQhJhTd 9s 2c")) == "AsKsQhJhTd9s2c",
          "смешанная запись: склеенные карты и отдельные")
    check(plain(cards("")) == "", "пустая строка — это пустой список карт")

    for bad_input in ["AhAh", "Zx", "Ah5", "A"]:
        try:
            cards(bad_input)
        except BadCard:
            continue
        check(False, "ввод «%s» должен быть отклонён" % bad_input)


def test_notation() -> None:
    check(hand_notation(cards("AsKs")) == "AKs", "AsKs → AKs")
    check(hand_notation(cards("KdAh")) == "AKo", "KdAh → AKo (туз первым)")
    check(hand_notation(cards("7h7d")) == "77", "7h7d → 77")


def run() -> int:
    print("Самопроверка покерного движка")
    print("-" * 46)
    for test in [
        test_ranking_order,
        test_tiebreakers,
        test_wheel,
        test_seven_cards,
        test_known_equities,
        test_split_pot,
        test_exact_matches_monte_carlo,
        test_outs,
        test_odds_math,
        test_parsing,
        test_notation,
    ]:
        test()
        print("  %-34s ok" % test.__name__)
    print("-" * 46)
    if _failures:
        print("\033[31mПровалено %d проверок из %d\033[0m" % (len(_failures), _checks))
        return 1
    print("\033[32mВсе %d проверок пройдены\033[0m" % _checks)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
