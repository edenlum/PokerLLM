import unittest
from agents.Player import Player

class TestPlayer(unittest.TestCase):
    def test_player_creation(self):
        player = Player('Alice', 1000)
        self.assertEqual(player.name, 'Alice')
        self.assertEqual(player.stack, 1000)
        self.assertEqual(player.hand, [])
        self.assertFalse(player.is_folded)
        self.assertFalse(player.is_all_in)
        self.assertEqual(player.current_bet, 0)

    def test_player_reset(self):
        player = Player('Bob', 500)
        player.hand = [1, 2]
        player.is_folded = True
        player.current_bet = 100
        player.reset_for_new_hand()
        self.assertEqual(player.hand, [])
        self.assertFalse(player.is_folded)
        self.assertEqual(player.current_bet, 0)

    def test_place_bet(self):
        player = Player('Charlie', 200)
        bet_amount = player.place_bet(50)
        self.assertEqual(player.stack, 150)
        self.assertEqual(player.current_bet, 50)
        self.assertEqual(bet_amount, 50)

    def test_place_bet_all_in(self):
        player = Player('David', 100)
        bet_amount = player.place_bet(150)  # Try to bet more than stack
        self.assertEqual(player.stack, 0)
        self.assertEqual(player.current_bet, 100)
        self.assertEqual(bet_amount, 100)
        self.assertTrue(player.is_all_in)

    def test_place_bet_zero(self):
        player = Player('Eve', 200)
        bet_amount = player.place_bet(0)
        self.assertEqual(player.stack, 200)
        self.assertEqual(player.current_bet, 0)
        self.assertEqual(bet_amount, 0)

if __name__ == '__main__':
    unittest.main()
