#!/usr/bin/env python3
"""Самопроверка: сверяет расчёты с известными покерными значениями.

Если этот файл проходит, калькуляторам можно доверять.
Запуск: python3 selftest.py   (или python3 poker.py test)
"""
from __future__ import annotations

import importlib
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import glossary
from core.cards import BadCard, full_deck, parse_cards as cards, plain, short_deck
from core.equity import equity, next_card_outs, pot_shares
from core.equity import exact_improve_chance, required_equity, rule_of_2_and_4
from core.evaluator import compare, describe, evaluate
from core.lowball import ace_to_five, badugi, deuce_to_seven, eight_or_better
from core.variant import HIGH, LOW, SPLIT

ALL_KEYS = ["texas_holdem", "omaha", "omaha_hi_lo", "short_deck",
            "five_card_draw", "seven_card_stud", "razz", "deuce_to_seven",
            "badugi"]

_failures = []
_checks = 0


def check(condition: bool, label: str) -> None:
    global _checks
    _checks += 1
    if not condition:
        _failures.append(label)
        print("  \033[31mFAIL\033[0m  %s" % label)


def check_close(actual: float, expected: float, tolerance: float,
                label: str) -> None:
    check(abs(actual - expected) <= tolerance,
          "%s: получено %.2f%%, ожидалось %.2f%% (±%.2f)"
          % (label, actual * 100, expected * 100, tolerance * 100))


def variant(key: str):
    return importlib.import_module("%s.rules" % key).VARIANT


# --------------------------------------------------------------------------
# Обычная оценка руки
# --------------------------------------------------------------------------

def test_ranking_order() -> None:
    """Комбинации должны строго убывать по силе."""
    ladder = ["AsKsQsJsTs", "7h7d7s7cKh", "AhAdAcKsKh", "Ah9h7h4h2h",
              "9s8d7h6c5s", "QhQdQc8s3h", "AsAhKdKc7h", "AsAhKdQc7h",
              "AsKdQh9c4s"]
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
    check(evaluate(cards("Ah5h4h3h2h"))[0] == 8,
          "A-2-3-4-5 одной масти — стрит-флеш")
    check(evaluate(cards("Ah5d4c3s2h"), wheel=False)[0] == 0,
          "без «колеса» A-2-3-4-5 должна быть просто старшей картой")


def test_seven_cards() -> None:
    """Из 7 карт должна выбираться лучшая пятёрка."""
    hand = cards("Ah2c") + cards("AsAd3h4s5c")
    check(evaluate(hand)[0] == 4,
          "стрит A-2-3-4-5 сильнее сета тузов: %s" % describe(hand))
    check(evaluate(cards("KhKd") + cards("KsAhAd2c3s"))[0] == 6,
          "должен собраться фулл-хаус")
    check(evaluate(cards("AhKh") + cards("QhJhTh3d4s"))[0] == 8,
          "должен найтись флеш-рояль")
    check(evaluate(cards("AhKh") + cards("QhJh2h3d4s"))[0] == 5,
          "A-K-Q-J-2 одной масти — это флеш, а не стрит-флеш")
    check(evaluate(cards("AhAd") + cards("AsKhKd2c3s"))[0] == 6,
          "две тройки в семи картах должны давать фулл-хаус")


# --------------------------------------------------------------------------
# Холдем: эталонные значения
# --------------------------------------------------------------------------

def test_known_equities() -> None:
    """Сверка с эталонными значениями.

    Первые четыре числа получены полным перебором всех возможных бордов
    (1 712 304 и 1 370 754 варианта) и совпадают с таблицами equity,
    которые публикуются в покерной литературе. Здесь они проверяются
    быстрым Монте-Карло, поэтому допуск — полтора процентных пункта.
    """
    holdem = variant("texas_holdem")
    check_close(equity(holdem, [cards("AsAh"), cards("KsKd")],
                       seed=1).hero_equity, 0.8195, 0.015, "AA против KK")
    check_close(equity(holdem, [cards("AhKh"), cards("2c2d")],
                       seed=2).hero_equity, 0.5008, 0.015, "AKs против 22")
    check_close(equity(holdem, [cards("AsKd"), cards("QsQd")],
                       seed=3).hero_equity, 0.4365, 0.015, "AKo против QQ")
    check_close(equity(holdem, [cards("AsAh"), cards("KsKd"), cards("QsQd")],
                       seed=6).hero_equity, 0.6745, 0.020, "AA против KK и QQ")
    check_close(equity(holdem, [cards("AsAh"), []], seed=4).hero_equity,
                0.852, 0.015, "AA против случайной руки")
    check_close(equity(holdem, [cards("7s2d"), []], seed=5).hero_equity,
                0.346, 0.020, "72o против случайной руки")


def test_split_pot() -> None:
    holdem = variant("texas_holdem")
    result = equity(holdem, [cards("AhKh"), cards("AsKs")], cards("2d7c9hTs4c"))
    check_close(result.hero_equity, 0.5, 0.001, "одинаковые руки делят банк")
    check(result.exact, "при полном борде должен использоваться точный перебор")
    check_close(result.hero_tie, 1.0, 0.001, "это ничья в 100% случаев")


def test_exact_matches_monte_carlo() -> None:
    holdem = variant("texas_holdem")
    hero, villain, board = cards("9h8h"), cards("KsQd"), cards("Kh7h2cAd")
    exact = equity(holdem, [hero, villain], board)
    check(exact.exact, "на тёрне перебор должен быть точным")
    monte = equity(holdem, [hero, villain], board, iterations=20000, seed=9)
    check_close(monte.hero_equity, exact.hero_equity, 0.02,
                "Монте-Карло близко к точному значению")


def test_outs() -> None:
    holdem = variant("texas_holdem")
    outs, _ties = next_card_outs(holdem, cards("9h8h"), cards("KsQd"),
                                 cards("Kh7h2c"))
    check(len(outs) == 9, "у флеш-дро 9 аутсов, найдено %d" % len(outs))
    check(all(card.suit == "h" for card in outs),
          "все аутсы флеш-дро должны быть червами")
    outs, _ties = next_card_outs(holdem, cards("9s8d"), cards("AhAc"),
                                 cards("7h Tc 2s"))
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
    check(plain(cards("AhKh")) == "AhKh", "слитная запись")
    check(plain(cards("As Kh")) == "AsKh", "запись через пробел")
    check(plain(cards("As, Kh, 10d")) == "AsKhTd", "запятые и «10» вместо T")
    check(plain(cards("AsKsQhJhTd 9s 2c")) == "AsKsQhJhTd9s2c",
          "смешанная запись: склеенные карты и отдельные")
    check(plain(cards("")) == "", "пустая строка — пустой список карт")
    for bad_input in ["AhAh", "Zx", "Ah5", "A"]:
        try:
            cards(bad_input)
        except BadCard:
            continue
        check(False, "ввод «%s» должен быть отклонён" % bad_input)


def test_notation() -> None:
    from texas_holdem.ranges import hand_notation
    check(hand_notation(cards("AsKs")) == "AKs", "AsKs → AKs")
    check(hand_notation(cards("KdAh")) == "AKo", "KdAh → AKo (туз первым)")
    check(hand_notation(cards("7h7d")) == "77", "7h7d → 77")


# --------------------------------------------------------------------------
# Омаха
# --------------------------------------------------------------------------

def test_omaha_exactly_two() -> None:
    """Правило «ровно две карты из руки» — главное в омахе."""
    omaha = variant("omaha")
    # Одна черва в руке и три на борде: флеша быть НЕ должно.
    score = omaha.evaluate_high(cards("Ah2s3d4c"), cards("Kh7h2h"))
    check(score[0] != 5, "одна черва в руке не даёт флеша в омахе")
    # Две червы в руке и три на борде: флеш должен быть.
    score = omaha.evaluate_high(cards("AhKh2s3c"), cards("Qh7h5h"))
    check(score[0] == 5, "две червы в руке и три на борде дают флеш")
    # Четыре карты в руке нельзя использовать целиком.
    score = omaha.evaluate_high(cards("AsKsQsJs"), cards("Ts2d3c"))
    check(score[0] != 8,
          "стрит-флеш из четырёх своих карт невозможен: нужно ровно две")


def test_omaha_hi_lo() -> None:
    o8 = variant("omaha_hi_lo")
    # Лоу есть: туз-двойка в руке, три низкие карты на борде.
    low = o8.evaluate_low(cards("As2d9hTc"), cards("3h4c7s9dQh"))
    check(low == (7, 4, 3, 2, 1), "A-2 с бордом 3-4-7 даёт лоу 7-4-3-2-A")
    # Лоу нет: на борде меньше трёх низких карт.
    low = o8.evaluate_low(cards("As2d9hTc"), cards("KdQh9sJhTd"))
    check(low is None, "без трёх низких карт на борде лоу не собрать")
    # Банк делится между хай и лоу.
    shares, had_low = pot_shares(
        o8, [cards("As2d9hTc"), cards("KsKhQdJc")], cards("3h4c7s9dKd"))
    check(had_low, "лоу в этой раздаче должно быть собрано")
    check_close(shares[0], 0.5, 0.001,
                "игрок с лоу, но без хая, забирает половину банка")

    # Быстрый расчёт лоу должен совпадать с медленным перебором карт.
    from omaha_hi_lo.rules import best_low, evaluate_low
    rng = random.Random(3)
    mismatches = 0
    for _ in range(600):
        deck = full_deck()
        rng.shuffle(deck)
        hole, board = deck[:4], deck[4:9]
        slow = best_low(hole, board)
        slow = None if slow is None else slow[0]
        if evaluate_low(hole, board) != slow:
            mismatches += 1
    check(mismatches == 0,
          "быстрый расчёт лоу должен совпадать с перебором карт "
          "(расхождений: %d)" % mismatches)


# --------------------------------------------------------------------------
# Шортдек
# --------------------------------------------------------------------------

def test_short_deck() -> None:
    from short_deck.rules import evaluate as sd_evaluate
    check(len(short_deck()) == 36, "в короткой колоде 36 карт")
    check(min(card.rank for card in short_deck()) == 6,
          "младшая карта короткой колоды — шестёрка")

    flush = cards("AhKh9h7h6h")
    ladder = [
        ("стрит-флеш", cards("Ah6h7h8h9h")),
        ("каре", cards("7h7d7s7cKh")),
        ("флеш", flush),
        ("фулл-хаус", cards("AsAhAdKsKh")),
        ("тройка", cards("9s9d9c7h6s")),
        ("стрит", cards("6s7d8h9cTs")),
        ("две пары", cards("AsAhKdKc7h")),
        ("пара", cards("AsAhKdQc7h")),
        ("старшая карта", cards("AsKdQh9c7s")),
    ]
    for (upper_name, upper), (lower_name, lower) in zip(ladder, ladder[1:]):
        check(sd_evaluate(upper) > sd_evaluate(lower),
              "в шортдеке %s должна быть сильнее, чем %s"
              % (upper_name, lower_name))
    check(sd_evaluate(cards("As6d7h8c9s"))[0] == 3,
          "A-6-7-8-9 — младший стрит шортдека")


# --------------------------------------------------------------------------
# Лоу-системы
# --------------------------------------------------------------------------

def test_ace_to_five() -> None:
    """Система A-5 (разз): меньше — лучше."""
    wheel = ace_to_five(cards("5s4h3d2cAs"))
    check(wheel < ace_to_five(cards("6s4h3d2cAs")),
          "колесо 5-4-3-2-A должно быть лучшим лоу")
    check(ace_to_five(cards("8s6h5d3cAs")) < ace_to_five(cards("8s7h5d3cAs")),
          "«восьмёрка-шесть» лучше «восьмёрки-семь»")
    check(ace_to_five(cards("Ks9h7d4c2s")) < ace_to_five(cards("AsAh5d4c3s")),
          "любая рука без пар лучше любой пары")
    check(ace_to_five(cards("5s4h3d2cAs")) == ace_to_five(cards("5d4c3h2sAd")),
          "масти в системе A-5 не имеют значения")
    check(ace_to_five(cards("9s8h7d6c5s")) == ace_to_five(cards("9s8h7d6c5h")),
          "стриты в системе A-5 не считаются")


def test_eight_or_better() -> None:
    check(eight_or_better(cards("5s4h3d2cAs")) == (5, 4, 3, 2, 1),
          "колесо проходит квалификацию 8 or better")
    check(eight_or_better(cards("9s8h7d6c5s")) is None,
          "девятка ломает квалификацию: нужны пять карт от восьмёрки и ниже")
    check(eight_or_better(cards("8s8h7d6c5s")) is None,
          "пара ломает квалификацию: нужны пять РАЗНЫХ карт")
    check(eight_or_better(cards("8s7h6d5c4s")) == (8, 7, 6, 5, 4),
          "8-7-6-5-4 — самое слабое проходящее лоу")


def test_deuce_to_seven() -> None:
    best = deuce_to_seven(cards("7s5h4d3c2s"))
    check(best < deuce_to_seven(cards("7s6h4d3c2s")),
          "7-5-4-3-2 — лучшая рука в 2-7")
    check(best < deuce_to_seven(cards("6s5h4d3c2s")),
          "6-5-4-3-2 это стрит, значит хуже 7-5-4-3-2")
    check(best < deuce_to_seven(cards("7s5s4s3s2s")),
          "7-5-4-3-2 одной масти это флеш, значит хуже")
    check(best < deuce_to_seven(cards("As5h4d3c2s")),
          "туз в 2-7 старший, поэтому A-5-4-3-2 хуже 7-5-4-3-2")
    check(deuce_to_seven(cards("6s5h4d3c2s"))[0] == 4,
          "6-5-4-3-2 должно опознаваться как стрит")


def test_badugi() -> None:
    best = badugi(cards("4s3h2dAc"))
    check(best == (0, 4, 3, 2, 1), "4-3-2-A четырёх мастей — лучшее бадуги")
    check(best < badugi(cards("7s5h3d2c")), "низкое бадуги лучше высокого")
    check(badugi(cards("Ks Qh Jd Tc")) < badugi(cards("4s3h2d2c")),
          "любое бадуги бьёт любой снаут")
    check(badugi(cards("4s3h2d2c"))[0] == 1,
          "пара превращает бадуги в снаут из трёх карт")
    check(badugi(cards("4s3h2dAs"))[0] == 1,
          "две карты одной масти тоже оставляют только снаут")
    check(badugi(cards("4s4h4d4c"))[0] == 3,
          "четыре одинаковых номинала дают всего одну работающую карту")


# --------------------------------------------------------------------------
# Общие свойства всех разновидностей
# --------------------------------------------------------------------------

def test_all_variants_consistent() -> None:
    """Свойства, которые обязаны выполняться в любой игре."""
    rng = random.Random(17)
    for key in ALL_KEYS:
        game = variant(key)
        check(game.mode in (HIGH, LOW, SPLIT),
              "%s: режим игры должен быть известен" % key)
        check(len(game.deck()) == len(set(game.deck())),
              "%s: в колоде не должно быть повторов" % key)
        if game.mode in (HIGH, SPLIT):
            check(game.evaluate_high is not None,
                  "%s: нужна оценка старшей руки" % key)
        if game.mode in (LOW, SPLIT):
            check(game.evaluate_low is not None,
                  "%s: нужна оценка младшей руки" % key)

        # Доли банка всегда должны складываться в единицу.
        deck = game.deck()
        rng.shuffle(deck)
        hands = [deck[:game.hole_size],
                 deck[game.hole_size:2 * game.hole_size]]
        board = deck[2 * game.hole_size:2 * game.hole_size + game.board_size]
        shares, _had_low = pot_shares(game, hands, board)
        check(abs(sum(shares) - 1.0) < 1e-9,
              "%s: доли банка должны складываться в 1, вышло %.6f"
              % (key, sum(shares)))

        # То же для расчёта equity: сумма по всем игрокам равна единице.
        result = equity(game, hands, board, iterations=400, seed=1)
        total = result.hero_equity + sum(result.villain_equities)
        check(abs(total - 1.0) < 1e-6,
              "%s: сумма equity всех игроков должна быть 1, вышло %.6f"
              % (key, total))

        # Описание руки не должно падать ни на полной, ни на пустой руке.
        try:
            game.describe(hands[0], board)
            game.describe([], [])
        except Exception as error:  # noqa: BLE001 — тест обязан поймать всё
            check(False, "%s: описание руки упало: %r" % (key, error))


def test_hand_generation() -> None:
    """Генератор рук для квизов должен выдавать заказанную комбинацию."""
    from core.drills import deal_with_category, straight_windows
    rng = random.Random(23)
    for key in ALL_KEYS:
        game = variant(key)
        if not game.category_shapes:
            continue
        check(len(straight_windows(game)) > 0,
              "%s: в колоде должны быть возможные стриты" % key)
        for target in game.category_order:
            deal = deal_with_category(game, target, rng)
            if deal is None:
                check(False, "%s: не удалось раздать комбинацию %s"
                             % (key, game.category_names[target]))
                continue
            hole, board = deal
            check(game.evaluate_high(hole, board)[0] == target,
                  "%s: заказана комбинация «%s», а вышла другая"
                  % (key, game.category_names[target]))


def test_glossary() -> None:
    check(len(glossary.TERM_LIST) >= 150,
          "в словаре должно быть не меньше 150 терминов, есть %d"
          % len(glossary.TERM_LIST))
    for term in glossary.TERM_LIST:
        check(term.group in glossary.GROUPS,
              "термин «%s» в неизвестной группе «%s»" % (term.name, term.group))
        check(bool(term.definition), "у термина «%s» нет определения" % term.name)
    for key in ALL_KEYS:
        for term_key in variant(key).terms:
            check(term_key in glossary.TERMS,
                  "%s ссылается на несуществующий термин «%s»" % (key, term_key))
    check(len(glossary.find("аутсы")) >= 1, "поиск должен находить «аутсы»")
    check(len(glossary.markdown()) > 10000, "GLOSSARY.md должен собираться")


TESTS = [
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
    test_omaha_exactly_two,
    test_omaha_hi_lo,
    test_short_deck,
    test_ace_to_five,
    test_eight_or_better,
    test_deuce_to_seven,
    test_badugi,
    test_all_variants_consistent,
    test_hand_generation,
    test_glossary,
]


def run() -> int:
    print("Самопроверка покерного движка")
    print("-" * 52)
    for test in TESTS:
        test()
        print("  %-40s ok" % test.__name__)
    print("-" * 52)
    if _failures:
        print("\033[31mПровалено %d проверок из %d\033[0m"
              % (len(_failures), _checks))
        return 1
    print("\033[32mВсе %d проверок пройдены\033[0m" % _checks)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
