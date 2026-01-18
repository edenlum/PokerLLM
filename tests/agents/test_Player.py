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

    def test_negative_raise_rejected(self):
        """Test that negative raise amounts are rejected."""
        player = Player('TestPlayer', 1000)
        
        # Test negative raise amount
        error = player.validate_action('raise', -10, ['fold', 'call', 'raise'], 50)
        self.assertIn("Amount must be positive for raise", error)
        self.assertNotEqual(error, "")  # Should have an error message
        
        # Test negative bet amount
        error = player.validate_action('bet', -5, ['check', 'bet'], 0)
        self.assertIn("Amount must be positive for bet", error)
        self.assertNotEqual(error, "")  # Should have an error message
        
        # Test zero raise amount (also should be rejected)
        error = player.validate_action('raise', 0, ['fold', 'call', 'raise'], 50)
        self.assertIn("Amount must be positive for raise", error)
        
        # Test zero bet amount (also should be rejected)
        error = player.validate_action('bet', 0, ['check', 'bet'], 0)
        self.assertIn("Amount must be positive for bet", error)

if __name__ == '__main__':
    unittest.main()
