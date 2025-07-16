import unittest
from simulator.Card import Card

class TestCard(unittest.TestCase):
    def test_card_creation(self):
        card = Card('♠', 'A')
        self.assertEqual(card.suit, '♠')
        self.assertEqual(card.rank, 'A')
        self.assertEqual(card.value, 14)

    def test_card_representation(self):
        card = Card('♥', 'K')
        self.assertEqual(str(card), 'K♥')
        self.assertEqual(repr(card), 'K♥')

if __name__ == '__main__':
    unittest.main()
