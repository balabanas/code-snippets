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
from collections import defaultdict


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


def kicker_ranks(ranked_hand):



def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    d: dict = {}
    it = itertools.combinations(hand, 5)
    for hand5 in it:
        d[hand5] = hand_rank(hand5)
    max_rank = max([v[0] for k, v in d.items()])
    d_max_rank = {k: v for k, v in d.items() if v[0] == max_rank}

    d = {}
    for k, rest in d_max_rank.items():
        rests_list = []
        for rest_component in rest[1:]:
            if isinstance(rest_component, (list, tuple)):
                rests_list.extend(rest_component)
            else:
                rests_list.append(rest_component)
        d[k] = rests_list

    # amount candidates of the same rank the len of rests returned by hand_rank is the same, so, take some one
    rests_dim = len(next(iter(d.values())))

    d_best_ranks: defaultdict = defaultdict(int)
    for criterion in range(rests_dim):
        for hand_candidate, rank_specific in d.items():
            d_best_ranks[hand_candidate] += rank_specific[criterion]
        max_value_unique = [None, 0, True]
        for k, v in d_best_ranks.items():
            if v > max_value_unique[1]:
                max_value_unique = [k, v, True]
            elif v == max_value_unique[1]:
                max_value_unique[2] = False
        if max_value_unique[2]:
            return list(max_value_unique[0])  # either found best
    return list(next(iter(d_best_ranks.keys())))  # either return an arbitrary hand out of candidates


def best_wild_hand(hand):
    """best_hand но с джокерами"""
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    black_suits = ['C', 'S']
    red_suits = ['H', 'D']
    black_deck = {r + s for r in ranks for s in black_suits}
    red_deck = {r + s for r in ranks for s in red_suits}

    stem = set(hand) - {'?B', '?R'}
    options = [list(stem), ]
    for joker, deck in [('?B', black_deck), ('?R', red_deck), ]:
        if joker in hand:
            complement_deck = deck - stem
            options = [(*a, b) for a, b in itertools.product(options, complement_deck)]

    d: dict = {}
    for option in options:
        it = itertools.combinations(option, 5)
        for hand5 in it:
            d[hand5] = hand_rank(hand5)

    max_rank = max([v[0] for k, v in d.items()])
    d_max_rank = {k: v for k, v in d.items() if v[0] == max_rank}

    d = {}
    for k, rest in d_max_rank.items():
        rests_list = []
        for rest_component in rest[1:]:
            if isinstance(rest_component, (list, tuple)):
                rests_list.extend(rest_component)
            else:
                rests_list.append(rest_component)
        d[k] = rests_list

    # amount candidates of the same rank the len of rests returned by hand_rank is the same, so, take some one
    rests_dim = len(next(iter(d.values())))

    d_best_ranks: defaultdict = defaultdict(int)
    for criterion in range(rests_dim):
        for hand_candidate, rank_specific in d.items():
            d_best_ranks[hand_candidate] += rank_specific[criterion]
        max_value_unique = [None, 0, True]
        for k, v in d_best_ranks.items():
            if v > max_value_unique[1]:
                max_value_unique = [k, v, True]
            elif v == max_value_unique[1]:
                max_value_unique[2] = False
        if max_value_unique[2]:
            return list(max_value_unique[0])  # either found best
    return list(next(iter(d_best_ranks.keys())))  # either return an arbitrary hand out of candidates


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
