import collections
from .Deck import Deck
from agents.Player import Player
from . import HandEvaluator

class Game:
    def __init__(self, players_data, small_blind=5, big_blind=10):
        self.players = [Player(name, stack) for name, stack in players_data]
        self.deck = Deck()
        self.pot = 0
        self.community_cards = []
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.dealer_pos = 0

    def run_hand(self):
        """Runs a single hand of poker."""
        self._setup_hand()
        self._run_betting_rounds()
        
        # Award pot if there are still active players (showdown scenario)
        active_players = [p for p in self.players if not p.is_folded]
        if len(active_players) > 1 and self.pot > 0:
            self._handle_showdown()
        elif len(active_players) == 1 and self.pot > 0:
            self._award_pot_to_winner()

    def _setup_hand(self):
        """Initializes a new hand."""
        self.pot = 0
        self.community_cards = []
        for player in self.players:
            player.reset_for_new_hand()
        self.deck = Deck()
        self.deck.shuffle()
        self.dealer_pos = (self.dealer_pos + 1) % len(self.players)
        self._post_blinds()
        self._deal_hole_cards()

    def _post_blinds(self):
        """Posts the small and big blinds."""
        sb_pos = (self.dealer_pos + 1) % len(self.players)
        bb_pos = (self.dealer_pos + 2) % len(self.players)
        self.pot += self.players[sb_pos].place_bet(self.small_blind)
        print(f"{self.players[sb_pos].name} posts small blind: {self.small_blind}")
        self.pot += self.players[bb_pos].place_bet(self.big_blind)
        print(f"{self.players[bb_pos].name} posts big blind: {self.big_blind}")

    def _deal_hole_cards(self):
        """Deals two hole cards to each player."""
        for player in self.players:
            player.hand.extend([self.deck.deal(), self.deck.deal()])

    def _deal_community_cards(self, count):
        """Deals a specified number of community cards."""
        self.community_cards.extend([self.deck.deal() for _ in range(count)])
        print(f"\nCommunity cards: {self.community_cards}")

    def _active_players_count(self):
        """Returns the number of players still in the hand."""
        # All-in players (stack=0 but is_all_in=True) should still be considered active
        return sum(1 for p in self.players if not p.is_folded)

    def _run_betting_rounds(self):
        """Runs all the betting rounds for a hand."""
        # Pre-flop
        if self._run_betting_round():
            # Flop
            self._deal_community_cards(3)
            if self._run_betting_round():
                # Turn
                self._deal_community_cards(1)
                if self._run_betting_round():
                    # River
                    self._deal_community_cards(1)
                    if self._run_betting_round():
                        self._handle_showdown()

    def _run_betting_round(self) -> bool:
        """Runs a single betting round."""
        if self._active_players_count() <= 1:
            print("No active players left, ending round.")
            return False

        is_pre_flop = len(self.community_cards) == 0
        if not is_pre_flop:
            for p in self.players:
                p.current_bet = 0
            amount_to_call = 0
            start_pos = (self.dealer_pos + 1) % len(self.players)
        else:
            amount_to_call = self.big_blind
            start_pos = (self.dealer_pos + 3) % len(self.players)

        players_to_act = collections.deque()
        for i in range(len(self.players)):
            player_pos = (start_pos + i) % len(self.players)
            player = self.players[player_pos]
            if not player.is_folded and not player.is_all_in:
                players_to_act.append(player)

        while players_to_act:
            player = players_to_act.popleft()

            if player.is_folded or player.is_all_in:
                continue

            if self._active_players_count() == 1:
                print(f"Only one player left, {player.name} wins the pot of {self.pot}!")
                self._award_pot_to_winner()
                return False

            legal_actions = self._get_legal_actions(player, amount_to_call)
            # Create game history for the player
            game_history = f"Current pot: {self.pot}, Community cards: {self.community_cards}"
            action, amount, is_fallback = player.get_action(game_history, legal_actions, amount_to_call)

            # Log fallback actions for analysis
            if is_fallback:
                if not hasattr(self, 'fallback_actions'):
                    self.fallback_actions = []
                self.fallback_actions.append({
                    'player': player.name,
                    'action': action,
                    'amount': amount,
                    'legal_actions': legal_actions.copy(),
                    'amount_to_call': amount_to_call
                })

            amount_to_call = self._handle_player_action(player, action, amount, players_to_act, amount_to_call)

        return self._active_players_count() > 1

    def _handle_player_action(self, player, action, amount, players_to_act, amount_to_call):
        """Handles a single player action."""
        if action == 'fold':
            player.is_folded = True
            print(f"{player.name} folds.")
        elif action == 'check':
            print(f"{player.name} checks.")
        elif action == 'call':
            to_bet = amount_to_call - player.current_bet
            self.pot += player.place_bet(to_bet)
            print(f"{player.name} calls.")
        elif action in ['bet', 'raise']:
            to_bet = amount - player.current_bet
            self.pot += player.place_bet(to_bet)
            amount_to_call = player.current_bet
            print(f"{player.name} {action}s to {amount_to_call}.")

            raiser_pos = self.players.index(player)
            players_to_act.clear()
            for i in range(1, len(self.players)):
                player_pos = (raiser_pos + i) % len(self.players)
                other_player = self.players[player_pos]
                if not other_player.is_folded and not other_player.is_all_in:
                    players_to_act.append(other_player)
        return amount_to_call

    def _get_legal_actions(self, player, amount_to_call):
        """Returns the legal actions for a player."""
        actions = []
        if amount_to_call > player.current_bet:
            actions.append('fold')
            if player.stack >= (amount_to_call - player.current_bet):
                actions.append('call')
            actions.append('raise')
        else:
            actions.append('check')
            actions.append('bet')
        return actions

    def _handle_showdown(self):
        """Handles the showdown at the end of a hand."""
        active_players = [p for p in self.players if not p.is_folded]
        winner = None
        best_hand_rank = -1
        best_tiebreaker = None

        print("\n--- Showdown ---")
        for player in active_players:
            hand_rank, tiebreaker = HandEvaluator.evaluate_hand(player.hand + self.community_cards)
            print(f"{player.name} has hand rank: {hand_rank} with tiebreaker: {tiebreaker}")
            if hand_rank > best_hand_rank:
                best_hand_rank = hand_rank
                best_tiebreaker = tiebreaker
                winner = [player]
            elif hand_rank == best_hand_rank:
                if tiebreaker > best_tiebreaker:
                    best_tiebreaker = tiebreaker
                    winner = [player]
                elif tiebreaker == best_tiebreaker:
                    winner.append(player)

        if len(winner) == 1:
            print(f"{winner[0].name} wins the pot of {self.pot}!")
            winner[0].stack += self.pot
        else:
            split_pot = self.pot / len(winner)
            print(f"Split pot! Winners: {[p.name for p in winner]}")
            for p in winner:
                p.stack += split_pot
        self.pot = 0

    def _award_pot_to_winner(self):
        """Awards the pot to the last remaining player."""
        winner = [p for p in self.players if not p.is_folded][0]
        print(f"{winner.name} wins the pot of {self.pot}!")
        winner.stack += self.pot
        self.pot = 0
