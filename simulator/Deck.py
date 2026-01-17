import random
from .Card import Card

class Deck:
    def __init__(self):
        self.cards = []
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]

    def shuffle(self, seed=None):
        """Shuffle the deck. If seed is provided, use it for reproducible shuffling."""
        if seed is not None:
            rng = random.Random(seed)
            rng.shuffle(self.cards)
        else:
            random.shuffle(self.cards)

    def deal(self):
        return self.cards.pop()
