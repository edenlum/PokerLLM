from itertools import combinations
from .Card import Card

def evaluate_hand(seven_cards):
    all_five_card_hands = combinations(seven_cards, 5)
    best_hand_rank = -1
    best_hand_tiebreaker = None

    for hand in all_five_card_hands:
        rank, tiebreaker = _get_hand_rank(hand)
        if rank > best_hand_rank:
            best_hand_rank = rank
            best_hand_tiebreaker = tiebreaker
        elif rank == best_hand_rank:
            if tiebreaker > best_hand_tiebreaker:
                best_hand_tiebreaker = tiebreaker

    return best_hand_rank, best_hand_tiebreaker

def _get_hand_rank(hand):
    values = sorted([card.value for card in hand], reverse=True)
    suits = [card.suit for card in hand]
    is_flush = len(set(suits)) == 1
    is_straight = (values[0] - values[4] == 4 and len(set(values)) == 5) or (values == [14, 5, 4, 3, 2])

    if is_straight and is_flush:
        return 9, tuple(values)

    rank_counts = {value: values.count(value) for value in values}
    sorted_rank_counts = sorted(rank_counts.items(), key=lambda item: (item[1], item[0]), reverse=True)

    if sorted_rank_counts[0][1] == 4:
        return 8, (sorted_rank_counts[0][0], sorted_rank_counts[1][0])

    if sorted_rank_counts[0][1] == 3 and sorted_rank_counts[1][1] == 2:
        return 7, (sorted_rank_counts[0][0], sorted_rank_counts[1][0])

    if is_flush:
        return 6, tuple(values)

    if is_straight:
        return 5, tuple(values)

    if sorted_rank_counts[0][1] == 3:
        kickers = tuple(sorted([v for v, c in sorted_rank_counts if c == 1], reverse=True))
        return 4, (sorted_rank_counts[0][0],) + kickers

    if sorted_rank_counts[0][1] == 2 and sorted_rank_counts[1][1] == 2:
        kicker = tuple(sorted([v for v, c in sorted_rank_counts if c == 1], reverse=True))
        pairs = tuple(sorted([v for v, c in sorted_rank_counts if c == 2], reverse=True))
        return 3, pairs + kicker

    if sorted_rank_counts[0][1] == 2:
        kickers = tuple(sorted([v for v, c in sorted_rank_counts if c == 1], reverse=True))
        return 2, (sorted_rank_counts[0][0],) + kickers

    return 1, tuple(values)
