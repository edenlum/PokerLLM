import unittest
from simulator.Deck import Deck
from simulator.Card import Card

class TestDeck(unittest.TestCase):
    def test_deck_creation(self):
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)
        self.assertIsInstance(deck.cards[0], Card)

    def test_deck_shuffle(self):
        deck1 = Deck()
        deck2 = Deck()
        deck2.shuffle()
        self.assertNotEqual(deck1.cards, deck2.cards)

    def test_deck_deal(self):
        deck = Deck()
        top_card = deck.cards[-1]
        dealt_card = deck.deal()
        self.assertEqual(dealt_card, top_card)
        self.assertEqual(len(deck.cards), 51)

if __name__ == '__main__':
    unittest.main()
