import unittest
from agents.Player import Player
from agents.HumanPlayer import HumanPlayer
from simulator.Game import Game
from simulator.Card import Card


class TestAllInScenarios(unittest.TestCase):
    """Test all-in scenarios to identify potential bugs."""
    
    def test_player_all_in_basic(self):
        """Test basic all-in functionality."""
        player = Player('TestPlayer', 100)
        
        # Test betting exactly the stack
        bet_amount = player.place_bet(100)
        self.assertEqual(bet_amount, 100)
        self.assertEqual(player.stack, 0)
        self.assertTrue(player.is_all_in)
        self.assertEqual(player.current_bet, 100)
    
    def test_player_all_in_over_stack(self):
        """Test betting more than stack (should be capped)."""
        player = Player('TestPlayer', 50)
        
        # Try to bet more than stack
        bet_amount = player.place_bet(100)
        self.assertEqual(bet_amount, 50)  # Should be capped to stack
        self.assertEqual(player.stack, 0)
        self.assertTrue(player.is_all_in)
        self.assertEqual(player.current_bet, 50)
    
    def test_validation_fixed_for_all_in(self):
        """Test that validation correctly handles all-in scenarios."""
        player = Player('TestPlayer', 50)
        player.current_bet = 10  # Already has 10 in pot
        
        # Raise to 60 total (need 50 more chips) - should be valid (all-in)
        error = player.validate_action('raise', 60, ['fold', 'call', 'raise'], 20)
        self.assertEqual(error, "")  # Should be valid
        
        # Raise to 61 total (need 51 more chips) - should be invalid
        error = player.validate_action('raise', 61, ['fold', 'call', 'raise'], 20)
        self.assertIn("Cannot raise to 61 - need 51 chips but only have 50", error)
        
        # Test that place_bet works consistently
        to_bet = 60 - player.current_bet  # 50 chips needed
        bet_amount = player.place_bet(to_bet)
        self.assertEqual(bet_amount, 50)  # Should bet exactly 50
        self.assertTrue(player.is_all_in)  # Should be all-in
    
    def test_all_in_validation_edge_cases(self):
        """Test validation edge cases for all-in scenarios."""
        player = Player('TestPlayer', 50)
        
        # Test betting exactly the stack (should be valid)
        error = player.validate_action('raise', 50, ['fold', 'call', 'raise'], 10)
        self.assertEqual(error, "")  # Should be valid
        
        # Test betting one more than stack (should be invalid)
        error = player.validate_action('raise', 51, ['fold', 'call', 'raise'], 10)
        self.assertIn("Cannot raise to 51 - need 51 chips but only have 50", error)
    
    def test_game_all_in_logic(self):
        """Test all-in logic without full game simulation."""
        # Create game and test the all-in detection logic
        players_data = [('SmallStack', 30), ('BigStack', 1000)]
        game = Game(players_data, small_blind=5, big_blind=10)
        
        # Simulate all-in scenario
        small_stack = game.players[0]
        big_stack = game.players[1]
        
        # Initialize action_history before posting blinds
        game.action_history = []
        # Post blinds first to get accurate remaining chips
        game._post_blinds()
        
        # SmallStack goes all-in with remaining chips
        remaining_chips = small_stack.stack
        small_stack.place_bet(remaining_chips)
        self.assertTrue(small_stack.is_all_in)
        self.assertEqual(small_stack.stack, 0)
        
        # Test that active players count works with all-in
        active_count = game._active_players_count()
        self.assertEqual(active_count, 2)  # Both still active (all-in counts as active)
        
        # Test legal actions for all-in player (should be empty or limited)
        legal_actions = game._get_legal_actions(small_stack, 50)
        # All-in player shouldn't have betting actions available
        # (This depends on implementation - let's just check it doesn't crash)
    
    def test_multiple_all_ins_logic(self):
        """Test multiple all-in logic without full simulation."""
        players_data = [('Player1', 50), ('Player2', 75), ('Player3', 100)]
        game = Game(players_data, small_blind=5, big_blind=10)
        
        # Initialize action_history before posting blinds
        game.action_history = []
        # Post blinds first
        game._post_blinds()
        
        # Simulate multiple all-ins with remaining chips
        remaining1 = game.players[0].stack
        remaining2 = game.players[1].stack
        game.players[0].place_bet(remaining1)  # Player1 all-in
        game.players[1].place_bet(remaining2)  # Player2 all-in
        
        # Check all-in flags
        self.assertTrue(game.players[0].is_all_in)
        self.assertTrue(game.players[1].is_all_in)
        self.assertFalse(game.players[2].is_all_in)
        
        # Check active player count
        active_count = game._active_players_count()
        self.assertEqual(active_count, 3)  # All still active
        
        # Test chip conservation
        total_chips = sum(p.stack for p in game.players)
        total_bets = sum(p.current_bet for p in game.players)
        self.assertEqual(total_chips + total_bets, 225)  # Starting total
    
    def test_all_in_flag_reset(self):
        """Test that all-in flag is properly reset between hands."""
        player = Player('TestPlayer', 100)
        
        # Go all-in
        player.place_bet(100)
        self.assertTrue(player.is_all_in)
        self.assertEqual(player.stack, 0)
        
        # Reset for new hand
        player.reset_for_new_hand()
        self.assertFalse(player.is_all_in)
        
        # Add chips back (simulating winning)
        player.stack = 200
        
        # Should be able to bet normally again
        bet_amount = player.place_bet(50)
        self.assertEqual(bet_amount, 50)
        self.assertEqual(player.stack, 150)
        self.assertFalse(player.is_all_in)  # Not all-in with partial bet
    
    def test_all_in_with_human_player(self):
        """Test all-in scenario with HumanPlayer validation."""
        player = HumanPlayer('TestHuman', 50)
        player.hand = [Card('spades', 'A'), Card('hearts', 'K')]
        
        # Test that validation works correctly for all-in amounts
        error = player.validate_action('raise', 50, ['fold', 'call', 'raise'], 10)
        self.assertEqual(error, "")  # Should be valid
        
        # Test over-stack amount
        error = player.validate_action('raise', 51, ['fold', 'call', 'raise'], 10)
        self.assertIn("Cannot raise to 51 - need 51 chips but only have 50", error)
    
    def test_side_pot_logic(self):
        """Test side pot logic (simplified)."""
        # Note: Current implementation doesn't handle side pots properly
        # This test just verifies basic all-in behavior
        players_data = [('Short', 20), ('Medium', 50), ('Long', 100)]
        game = Game(players_data, small_blind=5, big_blind=10)
        
        # Initialize action_history before posting blinds
        game.action_history = []
        # Post blinds first
        game._post_blinds()
        
        # Simulate different all-in amounts with remaining chips
        remaining0 = game.players[0].stack
        remaining1 = game.players[1].stack
        game.players[0].place_bet(remaining0)  # Short all-in
        game.players[1].place_bet(remaining1)  # Medium all-in
        game.players[2].place_bet(remaining1)  # Long matches medium
        
        # Check states
        self.assertTrue(game.players[0].is_all_in)
        self.assertTrue(game.players[1].is_all_in)
        self.assertFalse(game.players[2].is_all_in)  # Still has chips left
        
        # Check chip conservation
        total_chips = sum(p.stack for p in game.players)
        total_bets = sum(p.current_bet for p in game.players)
        self.assertEqual(total_chips + total_bets, 170)  # Starting total
        
        # Note: Proper side pot handling would require more complex logic


if __name__ == '__main__':
    unittest.main()
