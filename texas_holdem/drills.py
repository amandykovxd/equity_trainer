"""Тренажёры, специфичные для техасского холдема.

Универсальные квизы («кто выиграл банк», «назови комбинацию», «колл или
фолд») живут в core/drills.py и работают для всех разновидностей. Здесь
только то, что имеет смысл исключительно в холдеме: счёт аутсов против
известной руки и фильтр стартовых рук по таблице.
"""
from __future__ import annotations

import random
from typing import List, Optional, Tuple

from core import ui
from core.cards import Card, full_deck, pretty
from core.equity import equity, next_card_outs
from core.evaluator import describe, evaluate
from core.drills import report
from texas_holdem import ranges
from texas_holdem.rules import VARIANT


def deal_draw_spot(rng: random.Random) -> Tuple[List[Card], List[Card], List[Card]]:
    """Ситуация на флопе, где герой проигрывает, но имеет аутсы."""
    while True:
        deck = full_deck()
        rng.shuffle(deck)
        hero, villain, board = deck[:2], deck[2:4], deck[4:7]
        hero_score = evaluate(hero + board)
        villain_score = evaluate(villain + board)
        if hero_score >= villain_score:
            continue
        outs, _ties = next_card_outs(VARIANT, hero, villain, board)
        if 2 <= len(outs) <= 15:
            return hero, villain, board


def quiz_outs(rounds: int = 5, rng: Optional[random.Random] = None) -> None:
    """«Сколько у меня аутсов?» — счёт аутсов на флопе."""
    rng = rng or random.Random()
    ui.title("Квиз: посчитай аутсы")
    ui.para("""
        Во всех ситуациях ниже вы проигрываете прямо сейчас, но карты
        соперника вам открыты. Сколько карт тёрна сделают вашу руку
        сильнее его руки? Ответ в пределах ±1 считается верным:
        за столом важна оценка, а не точность до карты.

        Equity внизу ответа может заметно отличаться от «аутсы × 4»:
        правило считает только попадание в аут, а equity учитывает ещё
        и карты ривера, и то, что иногда рука выигрывает другим способом.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        hero, villain, board = deal_draw_spot(rng)
        outs, ties = next_card_outs(VARIANT, hero, villain, board)

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Ваши карты:      %s   (%s)" % (pretty(hero), describe(hero + board)))
        print("  Борд (флоп):     %s" % pretty(board))
        print("  Карты соперника: %s   (%s)"
              % (pretty(villain), describe(villain + board)))
        print()
        answer = ui.ask("Сколько у вас аутсов")
        if not answer.lstrip("-").isdigit():
            ui.bad("Нужно число — считаю как неверный ответ.")
            guess = -99
        else:
            guess = int(answer)

        if abs(guess - len(outs)) <= 1:
            correct += 1
            ui.good("Верно: аутсов %d." % len(outs))
        else:
            ui.bad("Аутсов %d, а не %d." % (len(outs), guess))
        print("     Аутсы: %s" % pretty(sorted(outs, key=lambda c: (-c.rank, c.suit))))
        if ties:
            print("     Ещё %d карт(ы) дают ничью: %s" % (len(ties), pretty(ties)))
        chance = equity(VARIANT, [hero, villain], board, iterations=4000)
        print("     Equity до ривера: %.1f%%  (правило 4: ~%d%%)"
              % (chance.hero_equity * 100, min(100, len(outs) * 4)))

    report(correct, rounds)


def quiz_preflop(rounds: int = 10, rng: Optional[random.Random] = None) -> None:
    """«Играть или сбросить?» — фильтр стартовых рук."""
    rng = rng or random.Random()
    ui.title("Квиз: стартовые руки")
    ui.para("""
        Вам сдали две карты, до вас никто не повышал. Повышать или
        сбрасывать? Ориентир — таблица из урока 6: группы «премиум»,
        «сильная» и «играбельная» играем, «мусор» сбрасываем.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        deck = full_deck()
        rng.shuffle(deck)
        hero = deck[:2]
        notation, tier, advice = ranges.advice_for(hero)

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Ваши карты: %s   (обозначение: %s)" % (pretty(hero), notation))
        print()
        answer = ui.ask_choice("Ваше решение: r — рейз, f — фолд", "rf")
        should_raise = tier != ranges.TIER_FOLD

        if (answer == "r") == should_raise:
            correct += 1
            ui.good("Верно. Группа: %s." % ranges.TIER_NAMES[tier])
        else:
            ui.bad("Группа: %s — здесь правильнее %s."
                   % (ranges.TIER_NAMES[tier], "рейз" if should_raise else "фолд"))
        ui.para(advice, indent=5)
        result = equity(VARIANT, [hero, []], iterations=3000)
        print("     Equity против одной случайной руки: %.1f%%"
              % (result.hero_equity * 100))

    report(correct, rounds)


def quiz_preflop(rounds: int = 10, rng: Optional[random.Random] = None) -> None:
    """«Играть или сбросить?» — фильтр стартовых рук."""
    rng = rng or random.Random()
    ui.title("Квиз: стартовые руки")
    ui.para("""
        Вам сдали две карты, до вас никто не повышал. Повышать или
        сбрасывать? Ориентир — таблица из урока 6: группы «премиум»,
        «сильная» и «играбельная» играем, «мусор» сбрасываем.
    """)
    correct = 0
    for round_number in range(1, rounds + 1):
        deck = full_deck()
        rng.shuffle(deck)
        hero = deck[:2]
        notation, tier, advice = ranges.advice_for(hero)

        ui.section("Вопрос %d из %d" % (round_number, rounds))
        print("  Ваши карты: %s   (обозначение: %s)" % (pretty(hero), notation))
        print()
        answer = ui.ask_choice("Ваше решение: r — рейз, f — фолд", "rf")
        should_raise = tier != ranges.TIER_FOLD

        if (answer == "r") == should_raise:
            correct += 1
            ui.good("Верно. Группа: %s." % ranges.TIER_NAMES[tier])
        else:
            ui.bad("Группа: %s — здесь правильнее %s."
                   % (ranges.TIER_NAMES[tier], "рейз" if should_raise else "фолд"))
        ui.para(advice, indent=5)
        result = equity(VARIANT, [hero, []], iterations=3000)
        print("     Equity против одной случайной руки: %.1f%%"
              % (result.hero_equity * 100))

    report(correct, rounds)


