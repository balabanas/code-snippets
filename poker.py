#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - десятка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокера.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertools.
# Можно свободно определять свои функции и т.п.
# -----------------
import itertools

# The constant to untie top-level ranks returned by hand_rank, by taking into account the `weight` of remaining cards
# We have at maximum 8 slots to evaluate: in case of rank 2 case we have (rank) (pair of ranks) (5 cards))
KICKER_MULTIPLIERS = [1e14, 1e12, 1e10, 1e8, 1e6, 1e4, 1e2, 1]

# Deck references
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
BLACK_SUITS = ['C', 'S']
RED_SUITS = ['H', 'D']
BLACK_DECK = {r + s for r in RANKS for s in BLACK_SUITS}
RED_DECK = {r + s for r in RANKS for s in RED_SUITS}


def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return 8, max(ranks)
    elif kind(4, ranks):
        return 7, kind(4, ranks), kind(1, ranks)
    elif kind(3, ranks) and kind(2, ranks):
        return 6, kind(3, ranks), kind(2, ranks)
    elif flush(hand):
        return 5, ranks
    elif straight(ranks):
        return 4, max(ranks)
    elif kind(3, ranks):
        return 3, kind(3, ranks), ranks
    elif two_pair(ranks):
        return 2, two_pair(ranks), ranks
    elif kind(2, ranks):
        return 1, kind(2, ranks), ranks
    else:
        return 0, ranks


def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему"""
    card_values_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                       'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    card_values = [card_values_map[card[0]] for card in hand]
    ranks = sorted(card_values, reverse=True)
    return ranks


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    return len(set([card[1] for card in hand])) == 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""
    rank_diffs = [s - f for f, s in itertools.pairwise(ranks)]
    return max([len(list(g)) for k, g in itertools.groupby(rank_diffs)]) == 4


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""
    counts = {k: len(list(g)) for k, g in itertools.groupby(ranks)}
    kinds = sorted([k for k, v in counts.items() if v == n], reverse=True)
    # print('kinds', kinds)
    return kinds[0] if kinds else None


def two_pair(ranks):
    """Если есть две пары, то возвращает два соответствующих ранга,
    иначе возвращает None"""
    counts = {k: len(list(g)) for k, g in itertools.groupby(ranks)}
    kinds = sorted([k for k, v in counts.items() if v == 2], reverse=True)  # max 2 pairs in a hand of 5
    return (kinds[0], kinds[1]) if kinds and len(kinds) == 2 else None


def flatten(input_tuple: tuple) -> list:
    """Convert tuples to a flat list. Input tuple may contain mix of integers, tuples and lists"""
    output_list = []
    for element in input_tuple:
        if isinstance(element, int):
            output_list.append(element)
        elif isinstance(element, list) or isinstance(element, tuple):
            output_list.extend(flatten(element))
    return output_list


def kicker_rank(ranked_hand):
    """Takes raw ranks, as produced by `hand_rank` (with main rank and a bunch of tuples,
    which are reflecting straights' and kinds' weights and kicker cards)
    and return a simple rank for a hand: a single number, directly comparable between hands.
    Main rank takes the highest register (multiplied by 1e14 from the constant), second number
    multiplied by 1e12, and so on. If the raw rank is short (like in straight flush - (8, max(ranks)),
    only first some multipliers are used, the rest are omitted"""
    rank = flatten(ranked_hand)
    return sum([rank * mult for rank, mult in zip(rank, KICKER_MULTIPLIERS)])


def rank5from7(hand7):
    """Creates combinatorial iterator of 5-card hand from 7-card hand and yields rank for each 5-card hand."""
    iter_comb5 = itertools.combinations(hand7, 5)
    for hand5 in iter_comb5:
        hand5_rank = hand_rank(hand5)
        yield hand5, kicker_rank(hand5_rank)


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    hands_ranked: dict = {}
    for hand5, rank in rank5from7(hand):
        hands_ranked[hand5] = rank
    return max(hands_ranked, key=hands_ranked.get)


def best_wild_hand(hand):
    """best_hand но с джокерами"""
    stem = set(hand) - {'?B', '?R'}
    options = [list(stem), ]
    for joker, deck in [('?B', BLACK_DECK), ('?R', RED_DECK), ]:
        if joker in hand:
            complement_deck = deck - stem
            options = [(*a, b) for a, b in itertools.product(options, complement_deck)]

    hands_ranked: dict = {}
    for option in options:
        for hand5, rank in rank5from7(option):
            hands_ranked[hand5] = rank
    return max(hands_ranked, key=hands_ranked.get)


def test_best_hand():
    print("test_best_hand...")
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


def test_best_wild_hand():
    print("test_best_wild_hand...")
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
