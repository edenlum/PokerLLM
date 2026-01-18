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
        self.bb_pos = len(self.players) - 1

    def run_hand(self, seed=None):
        """Runs a single hand of poker.
        
        Args:
            seed: Optional random seed for deck shuffle (for replaying hands)
        """
        self._setup_hand(seed=seed)
        self._run_betting_rounds()
        
        # Award pot if there are still active players (showdown scenario)
        active_players = [p for p in self.players if not p.is_folded]
        if len(active_players) > 1 and self.pot > 0:
            self._handle_showdown()
        elif len(active_players) == 1 and self.pot > 0:
            self._award_pot_to_winner()
    
    def _setup_hand(self, seed=None):
        """Initializes a new hand.
        
        Args:
            seed: Optional random seed for deck shuffle
        """
        self.pot = 0
        self.community_cards = []
        for player in self.players:
            player.reset_for_new_hand()
        
        self.deck = Deck()
        self.deck.shuffle(seed=seed)
        self.bb_pos = (self.bb_pos + 1) % len(self.players)  # Rotate BB position each hand
        # Simple action history: list of strings like "Preflop - player1 (SB) raises to 50"
        self.action_history = []
        self._post_blinds()
        self._deal_hole_cards()

    def _post_blinds(self):
        """Posts the small and big blinds."""
        # SB is always BB-1, dealer is BB-2 (or BB-1 in heads-up, but logic works)
        sb_pos = (self.bb_pos - 1) % len(self.players)
        self.pot += self.players[sb_pos].place_bet(self.small_blind)
        print(f"{self.players[sb_pos].name} posts small blind: {self.small_blind}")
        sb_position = self._get_player_position(self.players[sb_pos])
        self.action_history.append(f"Preflop - {self.players[sb_pos].name} ({sb_position}) posts small blind {self.small_blind}")
        self.pot += self.players[self.bb_pos].place_bet(self.big_blind)
        print(f"{self.players[self.bb_pos].name} posts big blind: {self.big_blind}")
        self.action_history.append(f"Preflop - {self.players[self.bb_pos].name} (BB) posts big blind {self.big_blind}")

    def _deal_hole_cards(self):
        """Deals two hole cards to each player, starting from the small blind."""
        # Cards are dealt starting from SB (which is BB-1)
        start_pos = (self.bb_pos - 1) % len(self.players)
        for i in range(len(self.players)):
            player_pos = (start_pos + i) % len(self.players)
            player = self.players[player_pos]
            player.hand.extend([self.deck.deal(), self.deck.deal()])

    def _deal_community_cards(self, count):
        """Deals a specified number of community cards."""
        new_cards = [self.deck.deal() for _ in range(count)]
        self.community_cards.extend(new_cards)
        print(f"\nCommunity cards: {self.community_cards}")
        
        # Add community cards to action history
        if len(self.community_cards) == 3:
            # Flop
            self.action_history.append(f"Flop - {', '.join(str(c) for c in new_cards)}")
        elif len(self.community_cards) == 4:
            # Turn
            self.action_history.append(f"Turn - {new_cards[0]}")
        elif len(self.community_cards) == 5:
            # River
            self.action_history.append(f"River - {new_cards[0]}")

    def _active_players_count(self):
        """Returns the number of players still in the hand."""
        # All-in players (stack=0 but is_all_in=True) should still be considered active
        return sum(1 for p in self.players if not p.is_folded)

    def _run_betting_rounds(self):
        """Runs all the betting rounds for a hand."""
        # Pre-flop
        if self._run_betting_round('Preflop'):
            # Flop
            self._deal_community_cards(3)
            if self._run_betting_round('Flop'):
                # Turn
                self._deal_community_cards(1)
                if self._run_betting_round('Turn'):
                    # River
                    self._deal_community_cards(1)
                    if self._run_betting_round('River'):
                        self._handle_showdown()

    def _run_betting_round(self, round_name: str) -> bool:
        """Runs a single betting round.
        
        Args:
            round_name: Name of the betting round (Preflop, Flop, Turn, River)
        """
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
            start_pos = (self.bb_pos - 1) % len(self.players)

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
            # Build game history from action history
            game_history = self._build_game_history(player, round_name, amount_to_call, legal_actions)
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

            amount_to_call = self._handle_player_action(player, action, amount, players_to_act, amount_to_call, round_name)

        return self._active_players_count() > 1

    @property
    def dealer_pos(self):
        """Dealer position computed from BB position for backward compatibility."""
        return (self.bb_pos - 1) % len(self.players) if len(self.players) == 2 else (self.bb_pos - 2) % len(self.players)

    def _get_player_position(self, player):
        """Get player's position relative to dealer.
        
        Uses BB position as base: SB = BB-1, dealer = BB-2 (or BB-1 in heads-up).
        In heads-up, dealer and SB are the same player, but the logic works correctly.
        """
        player_pos = self.players.index(player)
        utg_pos = (self.bb_pos + 1) % len(self.players)
        if player_pos == self.dealer_pos:
            return 'BTN'
        elif player_pos == self.bb_pos:
            return 'BB'
        elif player_pos == (self.bb_pos - 1) % len(self.players):
            return 'SB'
        elif player_pos == utg_pos:
            return 'UTG'
        else:
            return f'UTG{(player_pos - utg_pos) % len(self.players)}'
    
    def _build_game_history(self, current_player, current_round, amount_to_call, legal_actions):
        """Build structured game history string."""
        parts = []
        
        # General information
        parts.append(f"Players: {len(self.players)}")
        parts.append(f"Blinds: {self.small_blind}/{self.big_blind}")
        parts.append(f"Your position: {self._get_player_position(current_player)}")
        parts.append(f"Your hand: {current_player.hand}")
        parts.append("")
        
        # Action history grouped by stage
        current_stage = None
        for action_str in self.action_history:
            # Extract stage from action string (e.g., "Preflop - ..." -> "Preflop")
            if " - " in action_str:
                stage, action_part = action_str.split(" - ", 1)
            else:
                stage = current_round
                action_part = action_str
            
            # Check if this is a community card entry (no player name/parentheses)
            is_community_cards = "(" not in action_part
            
            if stage != current_stage:
                if current_stage is not None:
                    parts.append("")
                # Show community cards on the same line as stage name
                if is_community_cards:
                    parts.append(f"{stage}: {action_part}")
                else:
                    parts.append(f"{stage}:")
                current_stage = stage
                # Skip community card entries (already shown above)
                if is_community_cards:
                    continue
            
            # Skip community card entries (already shown above)
            if is_community_cards:
                continue
            
            # Replace player name with "You" only if this action was performed by current player
            if action_part.startswith(f"{current_player.name} ("):
                formatted_action = action_part.replace(f"{current_player.name} (", "You (", 1)
            else:
                formatted_action = action_part
            
            parts.append(f"  {formatted_action}")
        
        parts.append("")
        
        # Decision data
        parts.append(f"Total pot: {self.pot}")
        amount_to_call_net = amount_to_call - current_player.current_bet
        if amount_to_call_net > 0:
            parts.append(f"Amount to call: {amount_to_call_net}")
        if current_player.current_bet > 0:
            parts.append(f"Your current bet: {current_player.current_bet}")
        parts.append(f"Your stack: {current_player.stack}")
        parts.append(f"Legal actions: {', '.join(legal_actions)}")
        parts.append("")
        parts.append("What is your action?")
        
        return "\n".join(parts)
    
    def _handle_player_action(self, player, action, amount, players_to_act, amount_to_call, round_name):
        """Handles a single player action."""
        position = self._get_player_position(player)
        
        if action == 'fold':
            player.is_folded = True
            print(f"{player.name} folds.")
            self.action_history.append(f"{round_name} - {player.name} ({position}) folds")
        elif action == 'check':
            print(f"{player.name} checks.")
            self.action_history.append(f"{round_name} - {player.name} ({position}) checks")
        elif action == 'call':
            to_bet = amount_to_call - player.current_bet
            self.pot += player.place_bet(to_bet)
            print(f"{player.name} calls.")
            self.action_history.append(f"{round_name} - {player.name} ({position}) calls {amount_to_call}")
        elif action in ['bet', 'raise']:
            to_bet = amount - player.current_bet
            self.pot += player.place_bet(to_bet)
            amount_to_call = player.current_bet
            print(f"{player.name} {action}s to {amount_to_call}.")
            self.action_history.append(f"{round_name} - {player.name} ({position}) {action}s to {amount_to_call}")

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
