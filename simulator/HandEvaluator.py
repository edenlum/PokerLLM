from itertools import combinations
from enum import IntEnum
from .Card import Card


class HandRank(IntEnum):
    """Enum for poker hand rankings, ordered from weakest to strongest."""
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10  # Special case of straight flush
    
    def __str__(self):
        """Return human-readable name."""
        return self.name.lower().replace('_', ' ')
    
    @classmethod
    def from_int(cls, value: int):
        """Convert integer to HandRank for backward compatibility."""
        # Map old integer values to new enum values
        mapping = {
            1: cls.HIGH_CARD,
            2: cls.PAIR,
            3: cls.TWO_PAIR,
            4: cls.THREE_OF_A_KIND,
            5: cls.STRAIGHT,
            6: cls.FLUSH,
            7: cls.FULL_HOUSE,
            8: cls.FOUR_OF_A_KIND,
            9: cls.STRAIGHT_FLUSH,
            10: cls.ROYAL_FLUSH
        }
        return mapping.get(value, cls.HIGH_CARD)

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
        # Check for royal flush (A, K, Q, J, 10)
        if values == [14, 13, 12, 11, 10]:
            return HandRank.ROYAL_FLUSH, tuple(values)
        return HandRank.STRAIGHT_FLUSH, tuple(values)

    rank_counts = {value: values.count(value) for value in values}
    sorted_rank_counts = sorted(rank_counts.items(), key=lambda item: (item[1], item[0]), reverse=True)

    if sorted_rank_counts[0][1] == 4:
        return HandRank.FOUR_OF_A_KIND, (sorted_rank_counts[0][0], sorted_rank_counts[1][0])

    if sorted_rank_counts[0][1] == 3 and sorted_rank_counts[1][1] == 2:
        return HandRank.FULL_HOUSE, (sorted_rank_counts[0][0], sorted_rank_counts[1][0])

    if is_flush:
        return HandRank.FLUSH, tuple(values)

    if is_straight:
        return HandRank.STRAIGHT, tuple(values)

    if sorted_rank_counts[0][1] == 3:
        kickers = tuple(sorted([v for v, c in sorted_rank_counts if c == 1], reverse=True))
        return HandRank.THREE_OF_A_KIND, (sorted_rank_counts[0][0],) + kickers

    if sorted_rank_counts[0][1] == 2 and sorted_rank_counts[1][1] == 2:
        kicker = tuple(sorted([v for v, c in sorted_rank_counts if c == 1], reverse=True))
        pairs = tuple(sorted([v for v, c in sorted_rank_counts if c == 2], reverse=True))
        return HandRank.TWO_PAIR, pairs + kicker

    if sorted_rank_counts[0][1] == 2:
        kickers = tuple(sorted([v for v, c in sorted_rank_counts if c == 1], reverse=True))
        return HandRank.PAIR, (sorted_rank_counts[0][0],) + kickers

    return HandRank.HIGH_CARD, tuple(values)
