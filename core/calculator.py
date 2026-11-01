"""Разбор ситуации: equity, аутсы и решение по пот-оддсам.

Код здесь не знает, во что вы играете: он получает описание правил
(Variant) и работает одинаково для холдема, разза и бадуги. Каждая
разновидность добавляет к этому разбору свои пояснения — см. файлы
equity_calculator.py в папках разновидностей.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from . import ui
from .cards import Card, pretty
from .equity import (
    EquityResult,
    equity,
    pot_shares,
    exact_improve_chance,
    next_card_outs,
    required_equity,
    rule_of_2_and_4,
)
from .variant import LOW, SPLIT, Variant

Players = Sequence[Sequence[Card]]


def check_input(variant: Variant, players: Players, board: Sequence[Card]) -> None:
    """Проверяет ввод до того, как что-то посчитано и напечатано.

    Иначе пользователь увидит разбор руки, собранной из несуществующей
    колоды, и только потом сообщение об ошибке.
    """
    if len(players) < 2:
        raise ValueError("Нужны как минимум вы и один соперник.")
    seen = set()
    for index, hand in enumerate(players):
        if len(hand) > variant.hole_size:
            raise ValueError(
                "В «%s» у игрока не больше %d карт, а у игрока %d их %d."
                % (variant.name, variant.hole_size, index + 1, len(hand)))
        for card in hand:
            if card in seen:
                raise ValueError("Карта %s использована дважды." % (card,))
            seen.add(card)
    if len(board) > variant.board_size:
        if variant.board_size == 0:
            raise ValueError("В «%s» общих карт нет вообще." % variant.name)
        raise ValueError("В «%s» на борде не больше %d карт."
                         % (variant.name, variant.board_size))
    for card in board:
        if card in seen:
            raise ValueError("Карта %s использована дважды." % (card,))
        seen.add(card)
    allowed = set(variant.deck())
    for card in seen:
        if card not in allowed:
            raise ValueError("Карты %s нет в колоде «%s» (%d карт)."
                             % (card, variant.name, len(allowed)))


def show_situation(variant: Variant, players: Players,
                   board: Sequence[Card]) -> None:
    ui.section("Ситуация")
    if variant.board_size:
        stage = variant.board_stage(len(board))
        print("  Улица:      %s" % stage)
        print("  Борд:       %s" % pretty(board))
    hero = players[0]
    missing = variant.hole_size - len(hero)
    tail = ("   (ещё %d карт%s впереди)" % (missing, "а" if missing == 1 else "ы")
            if missing else "")
    print("  Ваши карты: %s%s" % (pretty(hero), tail))
    for index, villain in enumerate(players[1:], start=1):
        if not villain:
            print("  Соперник %d: карты неизвестны (считаем против любой руки)"
                  % index)
        else:
            unknown = variant.hole_size - len(villain)
            note = "   (+%d неизвестных)" % unknown if unknown else ""
            print("  Соперник %d: %s%s" % (index, pretty(villain), note))

    if len(hero) >= 5 or (variant.board_size and len(board) >= 3):
        print()
        print("  Сейчас у вас: %s%s%s"
              % (ui.BOLD, variant.describe(hero, board), ui.RESET))
        known = [v for v in players[1:] if len(v) == variant.hole_size]
        if len(known) == 1:
            print("  У соперника:  %s" % variant.describe(known[0], board))


def show_equity(variant: Variant, result: EquityResult) -> None:
    ui.section("Equity")
    print("  %s  %.1f%%" % (ui.bar(result.hero_equity, 30),
                            result.hero_equity * 100))
    print()
    print(result.summary(variant))
    if variant.mode == SPLIT:
        ui.hint("В хай-лоу половина банка достаётся сильнейшей руке, "
                "половина — слабейшей. Забрать обе половины называется "
                "«скуп», и именно к этому стоит стремиться: половина "
                "банка часто лишь возвращает вложенное.")
    elif variant.mode == LOW:
        ui.hint("Это игра на слабейшую руку: чем «хуже» ваши карты "
                "по обычным меркам, тем лучше.")


def show_outs(variant: Variant, players: Players,
              board: Sequence[Card]) -> None:
    """Аутсы — если ситуация позволяет их однозначно посчитать.

    Аутсы имеют смысл только когда до конца раздачи остаётся известное
    число карт и карты соперника известны. И только когда вы позади:
    если вы уже впереди, считать надо не аутсы, а опасные карты.
    """
    if len(players) != 2:
        return
    hero, villain = players[0], players[1]
    if len(villain) != variant.hole_size:
        return

    if variant.board_size:
        if len(hero) != variant.hole_size or not 3 <= len(board) <= 4:
            return
        cards_to_come = variant.board_size - len(board)
        where = "на борд"
    else:
        cards_to_come = variant.hole_size - len(hero)
        if cards_to_come != 1:
            return
        where = "вам в руку"

    # Кто впереди прямо сейчас.
    try:
        current, _had_low = pot_shares(variant, [hero, villain], board)
    except (ValueError, KeyError):
        return
    hero_ahead = current[0] > 0.5

    outs, ties = next_card_outs(variant, hero, villain, board)
    unseen = len(variant.deck()) - len(hero) - len(villain) - len(board)
    multiplier = 4 if cards_to_come >= 2 else 2

    if hero_ahead:
        ui.section("Опасные карты")
        danger = unseen - len(outs) - len(ties)
        print("  Вы впереди прямо сейчас, поэтому аутсы считает соперник, "
              "а не вы.")
        print("  Карт, после которых вперёд выходит он: %d из %d."
              % (danger, unseen))
        if cards_to_come == 1:
            print("  То есть вы остаётесь впереди примерно в %.0f%% случаев."
                  % ((unseen - danger) / unseen * 100))
        ui.hint("Когда вы впереди, задача обратная: брать деньги с соперника "
                "и не давать ему дешёвых карт. Поэтому с сильной рукой "
                "обычно ставят, а не ждут.")
        return

    ui.section("Аутсы")
    if outs:
        print("  Аутсов: %d — %s"
              % (len(outs), pretty(sorted(outs, key=lambda c: (-c.rank, c.suit)))))
        print("  Это карты, которые приходят %s и выводят вас вперёд." % where)
        print()
        print("  Правило %d: %d × %d = %.0f%%"
              % (multiplier, len(outs), multiplier,
                 rule_of_2_and_4(len(outs), cards_to_come) * 100))
        print("  Точная вероятность попасть: %.1f%%"
              % (exact_improve_chance(len(outs), unseen, cards_to_come) * 100))
    else:
        print("  Аутсов нет: ни одна карта не выводит вас вперёд.")
    if ties:
        print("  Ничья при: %s" % pretty(ties))
    if not variant.board_size:
        ui.hint("В стад- и дро-играх помните про мёртвые карты: если "
                "нужные вам карты уже лежат в открытых руках соперников, "
                "аутов на самом деле меньше.")


def show_pot_odds(result: EquityResult, pot: float, bet: float) -> None:
    need = required_equity(pot, bet)
    expected_value = result.hero_equity * (pot + bet) - bet
    ui.section("Решение по пот-оддсам")
    print("  В банке %.0f, ставка соперника %.0f." % (pot, bet))
    print("  Требуемая equity: %.1f%%   (%.0f / %.0f)"
          % (need * 100, bet, pot + bet))
    print("  Ваша equity:      %.1f%%" % (result.hero_equity * 100))
    print("  Ожидание колла:   %+.1f" % expected_value)
    print()
    if result.hero_equity > need:
        ui.good("Колл выгоден (+%.1f п.п. equity сверх требуемой)."
                % ((result.hero_equity - need) * 100))
    else:
        ui.bad("Колл убыточен (не хватает %.1f п.п. equity) — фолд."
               % ((need - result.hero_equity) * 100))
    ui.hint("Это расчёт только для колла. Рейз может быть выгоден и там, "
            "где колл убыточен — но это следующая ступень обучения.")


def analyze(
    variant: Variant,
    players: Players,
    board: Sequence[Card] = (),
    pot: Optional[float] = None,
    bet: Optional[float] = None,
    iterations: Optional[int] = None,
) -> EquityResult:
    """Полный разбор ситуации. Возвращает расчёт, чтобы его можно было
    дополнить пояснениями конкретной разновидности."""
    check_input(variant, players, board)
    show_situation(variant, players, board)
    result = equity(variant, players, board, iterations=iterations)
    show_equity(variant, result)
    show_outs(variant, players, board)
    if pot is not None and bet:
        show_pot_odds(result, pot, bet)
    return result
