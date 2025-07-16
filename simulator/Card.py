class Card:
    RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.value = self.RANK_VALUES[rank]

    def __repr__(self):
        return f"{self.rank}{self.suit}"
