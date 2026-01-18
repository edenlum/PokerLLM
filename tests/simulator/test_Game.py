import unittest
from simulator.Game import Game

class TestGame(unittest.TestCase):
    def test_game_creation(self):
        players_data = [('Alice', 1000), ('Bob', 1000)]
        game = Game(players_data)
        self.assertEqual(len(game.players), 2)
        self.assertEqual(game.players[0].name, 'Alice')
        self.assertEqual(game.small_blind, 5)
        self.assertEqual(game.big_blind, 10)

    def test_setup_hand(self):
        players_data = [('Alice', 1000), ('Bob', 1000), ('Charlie', 1000)]
        game = Game(players_data)
        game._setup_hand()

        self.assertEqual(game.pot, 15)
        self.assertEqual(len(game.community_cards), 0)
        self.assertEqual(len(game.players[0].hand), 2)
        self.assertEqual(len(game.players[1].hand), 2)
        self.assertEqual(len(game.players[2].hand), 2)
        self.assertEqual(game.players[2].current_bet, 5)
        self.assertEqual(game.players[0].current_bet, 10)

    def test_pre_flop_betting_all_fold_to_bb(self):
        players_data = [('Alice', 1000), ('Bob', 1000), ('Charlie', 1000)]
        game = Game(players_data)
        game._setup_hand()

        # Scripted actions: Bob folds, Charlie folds
        game.players[1].scripted_actions = [('fold', 0)]
        game.players[2].scripted_actions = [('fold', 0)]

        game._run_betting_round('Preflop')

        # Alice (BB) should win the pot
        self.assertEqual(game.players[0].stack, 1005) # 1000 - 10 (bb) + 15 (pot)
        self.assertEqual(game.players[1].stack, 1000)
        self.assertEqual(game.players[2].stack, 995)

    def test_post_flop_betting_check_around(self):
        players_data = [('Alice', 1000), ('Bob', 1000), ('Charlie', 1000)]
        game = Game(players_data)
        game._setup_hand()

        # Pre-flop: Bob calls, Charlie calls, Alice checks
        game.players[1].scripted_actions = [('call', 0)]
        game.players[2].scripted_actions = [('call', 0)]
        game.players[0].scripted_actions = [('check', 0)]
        game._run_betting_round('Preflop')

        game._deal_community_cards(3)

        # Post-flop: all check
        game.players[1].scripted_actions = [('check', 0)]
        game.players[2].scripted_actions = [('check', 0)]
        game.players[0].scripted_actions = [('check', 0)]
        game._run_betting_round('Flop')

        self.assertEqual(game.pot, 30)

    def test_bet_raise_and_call(self):
        players_data = [('Alice', 1000), ('Bob', 1000), ('Charlie', 1000)]
        game = Game(players_data)
        game._setup_hand()

        # Pre-flop actions
        game.players[1].scripted_actions = [('call', 0)]
        game.players[2].scripted_actions = [('raise', 30)]
        game.players[0].scripted_actions = [('call', 0)]
        game.players[1].scripted_actions.append(('call', 0))

        game._run_betting_round('Preflop')

        self.assertEqual(game.pot, 90)
        self.assertEqual(game.players[0].stack, 970)
        self.assertEqual(game.players[1].stack, 970)
        self.assertEqual(game.players[2].stack, 970)

    def test_bet_option_on_new_street(self):
        players_data = [('Alice', 1000), ('Bob', 1000), ('Charlie', 1000)]
        game = Game(players_data)
        game._setup_hand()

        # Pre-flop: all check/call to get to the flop
        game.players[1].scripted_actions = [('call', 0)]
        game.players[2].scripted_actions = [('call', 0)]
        game.players[0].scripted_actions = [('check', 0)]
        game._run_betting_round('Preflop')

        # Deal flop
        game._deal_community_cards(3)

        # Now, on the flop, the first player to act should have 'bet' as a legal action
        # We need to simulate the turn for the first player to act in the new round
        # For simplicity, let's assume Alice is first to act after the flop
        # and check her legal actions.
        # In a real game, the player after the dealer button acts first post-flop.
        # Here, we'll just check one player's legal actions.
        first_player_post_flop = game.players[(game.dealer_pos + 1) % len(game.players)]
        legal_actions = game._get_legal_actions(first_player_post_flop, 0) # amount_to_call should be 0 at start of new street
        self.assertIn('bet', legal_actions)
        self.assertIn('check', legal_actions)
        self.assertNotIn('call', legal_actions)
        self.assertNotIn('raise', legal_actions)

if __name__ == '__main__':
    unittest.main()