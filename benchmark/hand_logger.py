"""
Hand Logger for capturing detailed poker hand information.
This keeps the core game logic separate from logging concerns.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from simulator import HandEvaluator


class HandLogger:
    """
    Captures detailed information about poker hands by observing game state.
    This class wraps around the Game class to add logging without modifying core game logic.
    """
    
    def __init__(self, game):
        """
        Initialize the hand logger.
        
        Args:
            game: The Game instance to observe
        """
        self.game = game
        self.hand_logs = []
        self.current_hand = None
        self.hand_number = 0
        
        # Store original methods to wrap them
        self._original_run_hand = game.run_hand
        self._original_get_action = None
        
        # Wrap the game methods
        self._wrap_game_methods()
    
    def _wrap_game_methods(self):
        """Wrap game methods to capture hand information."""
        
        # Wrap run_hand to capture hand start/end
        def wrapped_run_hand():
            self._start_hand()
            result = self._original_run_hand()
            self._end_hand()
            return result
        
        self.game.run_hand = wrapped_run_hand
        
        # Wrap player get_action methods to capture actions and reasoning
        for player in self.game.players:
            original_get_action = player.get_action
            
            def make_wrapped_get_action(p, orig_method):
                def wrapped_get_action(game_history, legal_actions, amount_to_call):
                    # Get the action from the player
                    action, amount, is_fallback = orig_method(game_history, legal_actions, amount_to_call)
                    
                    # Capture reasoning if available (for AI players)
                    reasoning = None
                    if hasattr(p, '_last_reasoning'):
                        reasoning = p._last_reasoning
                    
                    # Log the action
                    self._log_action(p, action, amount, is_fallback, reasoning, game_history)
                    
                    return action, amount, is_fallback
                
                return wrapped_get_action
            
            player.get_action = make_wrapped_get_action(player, original_get_action)
    
    def _start_hand(self):
        """Initialize logging for a new hand."""
        self.hand_number += 1
        
        # Capture initial state
        self.current_hand = {
            'hand_number': self.hand_number,
            'players': [p.name for p in self.game.players],
            'initial_stacks': {p.name: p.stack for p in self.game.players},
            'small_blind': self.game.small_blind,
            'big_blind': self.game.big_blind,
            'dealer_position': self.game.dealer_pos,
            'start_time': datetime.now().isoformat(),
            'actions': [],
            'game_events': []
        }
    
    def _log_action(self, player, action, amount, is_fallback, reasoning, game_history):
        """Log a player action with context."""
        if not self.current_hand:
            return
        
        action_log = {
            'player': player.name,
            'action': action,
            'amount': amount,
            'is_fallback': is_fallback,
            'reasoning': reasoning,
            'game_state': {
                'pot': self.game.pot,
                'community_cards': [str(card) for card in self.game.community_cards],
                'player_stack': player.stack,
                'player_current_bet': player.current_bet,
                'is_folded': player.is_folded,
                'is_all_in': player.is_all_in
            },
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_hand['actions'].append(action_log)
    
    def _end_hand(self):
        """Finalize the current hand log."""
        if not self.current_hand:
            return
        
        # Capture final state
        self.current_hand.update({
            'end_time': datetime.now().isoformat(),
            'final_stacks': {p.name: p.stack for p in self.game.players},
            'final_pot': self.game.pot,
            'community_cards': [str(card) for card in self.game.community_cards],
            'hole_cards': {p.name: [str(card) for card in p.hand] for p in self.game.players},
            'folded_players': [p.name for p in self.game.players if p.is_folded],
            'all_in_players': [p.name for p in self.game.players if p.is_all_in]
        })
        
        # Calculate results
        self._calculate_hand_results()
        
        # Store the completed hand
        self.hand_logs.append(self.current_hand.copy())
        self.current_hand = None
    
    def _calculate_hand_results(self):
        """Calculate hand results and statistics."""
        if not self.current_hand:
            return
        
        # Calculate winnings for each player
        winnings = {}
        for player_name in self.current_hand['players']:
            initial = self.current_hand['initial_stacks'][player_name]
            final = self.current_hand['final_stacks'][player_name]
            winnings[player_name] = final - initial
        
        self.current_hand['winnings'] = winnings
        
        # Determine winner(s)
        max_winnings = max(winnings.values())
        if max_winnings > 0:
            winners = [name for name, w in winnings.items() if w == max_winnings]
            self.current_hand['winners'] = winners
            self.current_hand['winner_type'] = 'split' if len(winners) > 1 else 'single'
        else:
            self.current_hand['winners'] = []
            self.current_hand['winner_type'] = 'none'
        
        # Determine if hand went to showdown
        active_players = [name for name in self.current_hand['players'] 
                         if name not in self.current_hand['folded_players']]
        self.current_hand['showdown'] = len(active_players) > 1
        
        # Evaluate hand strengths for showdown hands
        if self.current_hand['showdown'] and len(self.current_hand['community_cards']) >= 3:
            self._evaluate_hand_strengths()
        
        # Calculate statistics
        self.current_hand['stats'] = {
            'total_actions': len(self.current_hand['actions']),
            'fallback_actions': sum(1 for a in self.current_hand['actions'] if a['is_fallback']),
            'pot_size': self.current_hand['final_pot'],
            'hands_to_showdown': self.current_hand['showdown']
        }
    
    def _evaluate_hand_strengths(self):
        """Evaluate the strength of each player's hand."""
        hand_strengths = {}
        
        for player in self.game.players:
            if player.name in self.current_hand['folded_players']:
                hand_strengths[player.name] = 'folded'
                continue
            
            try:
                all_cards = player.hand + self.game.community_cards
                if len(all_cards) >= 5:
                    hand_rank, tiebreaker = HandEvaluator.evaluate_hand(all_cards)
                    
                    # Convert hand rank to readable string
                    hand_names = [
                        'high_card', 'pair', 'two_pair', 'three_of_a_kind',
                        'straight', 'flush', 'full_house', 'four_of_a_kind',
                        'straight_flush', 'royal_flush'
                    ]
                    
                    if 0 <= hand_rank < len(hand_names):
                        strength = hand_names[hand_rank]
                    else:
                        strength = f'rank_{hand_rank}'
                    
                    hand_strengths[player.name] = {
                        'strength': strength,
                        'rank': hand_rank,
                        'tiebreaker': tiebreaker
                    }
                else:
                    hand_strengths[player.name] = 'incomplete'
            except Exception:
                hand_strengths[player.name] = 'unknown'
        
        self.current_hand['hand_strengths'] = hand_strengths
    
    def get_hand_logs(self) -> List[Dict[str, Any]]:
        """Get all captured hand logs."""
        return self.hand_logs.copy()
    
    def get_last_hand(self) -> Optional[Dict[str, Any]]:
        """Get the most recent completed hand."""
        return self.hand_logs[-1].copy() if self.hand_logs else None
    
    def clear_logs(self):
        """Clear all captured hand logs."""
        self.hand_logs.clear()
        self.hand_number = 0
    
    def to_database_format(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Convert hand logs to database format.
        
        Args:
            session_id: The session ID to associate with these hands
            
        Returns:
            List of hand logs in database format
        """
        db_hands = []
        
        for hand in self.hand_logs:
            # For heads-up games, assume first two players
            players = hand['players']
            if len(players) < 2:
                continue
            
            player1, player2 = players[0], players[1]
            
            # Determine winner in database format
            winners = hand.get('winners', [])
            if len(winners) == 1:
                if winners[0] == player1:
                    winner = 'llm1'
                elif winners[0] == player2:
                    winner = 'llm2'
                else:
                    winner = 'unknown'
            elif len(winners) > 1:
                winner = 'split'
            else:
                winner = 'none'
            
            # Get hand strengths
            hand_strengths = hand.get('hand_strengths', {})
            strength1 = hand_strengths.get(player1, {})
            strength2 = hand_strengths.get(player2, {})
            
            if isinstance(strength1, dict):
                strength1 = strength1.get('strength', 'unknown')
            if isinstance(strength2, dict):
                strength2 = strength2.get('strength', 'unknown')
            
            db_hand = {
                'session_id': session_id,
                'hand_number': hand['hand_number'],
                'llm1_name': player1,
                'llm2_name': player2,
                'llm1_hole_cards': json.dumps(hand['hole_cards'].get(player1, [])),
                'llm2_hole_cards': json.dumps(hand['hole_cards'].get(player2, [])),
                'community_cards': json.dumps(hand['community_cards']),
                'actions': json.dumps(hand['actions']),
                'pot_size': hand['final_pot'],
                'winner': winner,
                'llm1_winnings': hand['winnings'].get(player1, 0.0),
                'llm2_winnings': hand['winnings'].get(player2, 0.0),
                'hand_date': hand['start_time'],
                'showdown': hand['showdown'],
                'hand_strength_llm1': strength1,
                'hand_strength_llm2': strength2
            }
            
            db_hands.append(db_hand)
        
        return db_hands
