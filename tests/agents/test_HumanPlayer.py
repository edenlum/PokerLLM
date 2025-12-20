import unittest
from unittest.mock import patch
from agents.HumanPlayer import HumanPlayer
from simulator.Card import Card

class TestHumanPlayer(unittest.TestCase):
    def setUp(self):
        self.player = HumanPlayer('TestPlayer', 1000)
        self.player.hand = [Card('♠', 'A'), Card('♥', 'K')]

    @patch('builtins.input', side_effect=['fold'])
    def test_fold_action(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['fold', 'call', 'raise'], 10)
        self.assertEqual(action, 'fold')
        self.assertEqual(amount, 0)

    @patch('builtins.input', side_effect=['call'])
    def test_call_action(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['fold', 'call', 'raise'], 10)
        self.assertEqual(action, 'call')
        self.assertEqual(amount, 0)

    @patch('builtins.input', side_effect=['raise 50'])
    def test_raise_action(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['fold', 'call', 'raise'], 10)
        self.assertEqual(action, 'raise')
        self.assertEqual(amount, 50)

    @patch('builtins.input', side_effect=['bet 100'])
    def test_bet_action(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['check', 'bet'], 0)
        self.assertEqual(action, 'bet')
        self.assertEqual(amount, 100)

    @patch('builtins.input', side_effect=['raise', 'raise 50'])
    def test_raise_without_amount(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['fold', 'call', 'raise'], 10)
        self.assertEqual(action, 'raise')
        self.assertEqual(amount, 50)

    @patch('builtins.input', side_effect=['raise 10000', 'raise 50'])
    def test_raise_more_than_stack(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['fold', 'call', 'raise'], 10)
        self.assertEqual(action, 'raise')
        self.assertEqual(amount, 50)

    @patch('builtins.input', side_effect=['raise 5', 'raise 50'])
    def test_raise_less_than_amount_to_call(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['fold', 'call', 'raise'], 10)
        self.assertEqual(action, 'raise')
        self.assertEqual(amount, 50)

    @patch('builtins.input', side_effect=['invalid', 'fold'])
    def test_invalid_action(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['fold', 'call', 'raise'], 10)
        self.assertEqual(action, 'fold')
        self.assertEqual(amount, 0)

    @patch('builtins.input', side_effect=['bet abc', 'bet 10'])
    def test_invalid_amount_type(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['check', 'bet'], 0)
        self.assertEqual(action, 'bet')
        self.assertEqual(amount, 10)

    @patch('builtins.input', side_effect=['bet -10', 'bet 20'])
    def test_negative_bet_amount(self, mock_input):
        action, amount = self.player.get_action("Test game history", ['check', 'bet'], 0)
        self.assertEqual(action, 'bet')
        self.assertEqual(amount, 20)

if __name__ == '__main__':
    unittest.main()