import unittest
from simulator.HandEvaluator import evaluate_hand
from simulator.Card import Card

class TestHandEvaluator(unittest.TestCase):
    def test_high_card(self):
        hand = [Card('♠', 'A'), Card('♥', 'K'), Card('♦', 'Q'), Card('♣', 'J'), Card('♠', '9'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 1)
        self.assertEqual(tiebreaker, (14, 13, 12, 11, 9))

    def test_pair(self):
        hand = [Card('♠', 'A'), Card('♥', 'A'), Card('♦', 'Q'), Card('♣', 'J'), Card('♠', '9'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 2)
        self.assertEqual(tiebreaker, (14, 12, 11, 9))

    def test_two_pair(self):
        hand = [Card('♠', 'A'), Card('♥', 'A'), Card('♦', 'Q'), Card('♣', 'Q'), Card('♠', '9'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 3)
        self.assertEqual(tiebreaker, (14, 12, 9))

    def test_three_of_a_kind(self):
        hand = [Card('♠', 'A'), Card('♥', 'A'), Card('♦', 'A'), Card('♣', 'J'), Card('♠', '9'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 4)
        self.assertEqual(tiebreaker, (14, 11, 9))

    def test_straight(self):
        hand = [Card('♠', 'T'), Card('♥', '9'), Card('♦', '8'), Card('♣', '7'), Card('♠', '6'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 5)
        self.assertEqual(tiebreaker, (10, 9, 8, 7, 6))

    def test_flush(self):
        hand = [Card('♠', 'A'), Card('♠', 'K'), Card('♠', 'Q'), Card('♠', 'J'), Card('♠', '9'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 6)
        self.assertEqual(tiebreaker, (14, 13, 12, 11, 9))

    def test_full_house(self):
        hand = [Card('♠', 'A'), Card('♥', 'A'), Card('♦', 'A'), Card('♣', 'K'), Card('♠', 'K'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 7)
        self.assertEqual(tiebreaker, (14, 13))

    def test_four_of_a_kind(self):
        hand = [Card('♠', 'A'), Card('♥', 'A'), Card('♦', 'A'), Card('♣', 'A'), Card('♠', 'K'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 8)
        self.assertEqual(tiebreaker, (14, 13))

    def test_straight_flush(self):
        hand = [Card('♠', 'T'), Card('♠', '9'), Card('♠', '8'), Card('♠', '7'), Card('♠', '6'), Card('♥', '2'), Card('♦', '3')]
        rank, tiebreaker = evaluate_hand(hand)
        self.assertEqual(rank, 9)
        self.assertEqual(tiebreaker, (10, 9, 8, 7, 6))

if __name__ == '__main__':
    unittest.main()
