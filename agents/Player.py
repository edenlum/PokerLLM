# Card import removed - not used in base Player class
from pydantic import BaseModel, Field
from typing import Literal


class Player:
    def __init__(self, name, stack):
        self.name = name
        self.stack = stack
        self.hand = []
        self.is_folded = False
        self.is_all_in = False
        self.current_bet = 0
        self.scripted_actions = []
        
    def validate_action(self, action: str, amount: int, legal_actions: list, amount_to_call: int) -> str:
        """
        Validate an action and amount. Returns error message if invalid, empty string if valid.
        
        Args:
            action: The action string
            amount: The amount for bet/raise actions
            legal_actions: List of valid actions
            amount_to_call: Amount needed to call
            
        Returns:
            Error message string (empty if valid)
        """
        # Validate action is legal
        if action not in legal_actions:
            return f"Invalid action '{action}'. Legal actions: {legal_actions}"
        
        # Validate amount constraints
        if action in ['bet', 'raise']:
            if amount <= 0:
                return f"Amount must be positive for {action}"
            
            if action == 'raise' and amount <= amount_to_call:
                return f"Raise amount ({amount}) must be greater than amount to call ({amount_to_call})"
            
            # Calculate actual chips needed (this is what the game will actually bet)
            chips_needed = amount - self.current_bet
            if chips_needed > self.stack:
                return f"Cannot {action} to {amount} - need {chips_needed} chips but only have {self.stack}"
            
            # Check minimum bet/raise sizes
            if action == 'bet' and amount_to_call > 0:
                return "Cannot bet when there's already a bet to call. Use 'raise' instead."
        
        elif action in ['call', 'check', 'fold']:
            # These actions should have amount = 0
            if amount != 0:
                return f"Action '{action}' should not have an amount"
        
        return ""  # Valid action

    def get_action_with_validation(self, game_history, legal_actions, amount_to_call, error_message: str = "", debug: bool = False) -> tuple[str, int, bool]:
        """
        Get player action with validation and retry logic.
        This calls the subclass's get_raw_action method and validates the result.
        
        Args:
            debug: If True, print detailed debugging information
        
        Returns:
            tuple: (action, amount, is_fallback) - is_fallback=True if this was a fallback action
        """
        max_attempts = 5
        validation_errors = []  # Track all validation errors for debugging
        
        if debug:
            print(f"\n🔍 DEBUG {self.name}: Starting action validation")
            print(f"   Legal actions: {legal_actions}")
            print(f"   Amount to call: {amount_to_call}")
            print(f"   Player stack: {self.stack}")
            print(f"   Current bet: {self.current_bet}")
        
        for attempt in range(max_attempts):
            try:
                # Get raw action from subclass
                action, amount = self.get_raw_action(game_history, legal_actions, amount_to_call, error_message)
                
                if debug:
                    print(f"   Attempt {attempt + 1}: Got action='{action}', amount={amount}")
                
                # Validate the action
                error_message = self.validate_action(action, amount, legal_actions, amount_to_call)
                
                if not error_message:
                    # Valid action, return it (not a fallback)
                    if debug:
                        print(f"   ✅ Action validated successfully!")
                    return action, amount, False
                
                # Invalid action, track error and retry
                validation_errors.append({
                    'attempt': attempt + 1,
                    'action': action,
                    'amount': amount,
                    'error': error_message
                })
                
                if debug:
                    print(f"   ❌ Validation failed: {error_message}")
                
            except Exception as e:
                # Error getting raw action (e.g., AI API failure)
                error_message = f"Error getting action: {str(e)}"
                validation_errors.append({
                    'attempt': attempt + 1,
                    'action': 'EXCEPTION',
                    'amount': 'N/A',
                    'error': error_message
                })
                
                if debug:
                    print(f"   💥 Exception on attempt {attempt + 1}: {str(e)}")
        
        # All attempts failed - use fallback action
        print(f"⚠️  {self.name}: Validation failed after {max_attempts} attempts. Using fallback action.")
        
        # Store validation errors for debugging
        if not hasattr(self, '_validation_failures'):
            self._validation_failures = []
        self._validation_failures.append({
            'game_state': {
                'legal_actions': legal_actions,
                'amount_to_call': amount_to_call,
                'player_stack': self.stack,
                'current_bet': self.current_bet
            },
            'errors': validation_errors
        })
        
        if debug:
            print(f"   🔍 All validation errors:")
            for i, error in enumerate(validation_errors, 1):
                print(f"      {i}. {error['action']} {error['amount']} -> {error['error']}")
        
        # Choose safe fallback: check if possible, otherwise fold
        if "check" in legal_actions:
            fallback_action = "check"
            fallback_amount = 0
        else:
            fallback_action = "fold"
            fallback_amount = 0
        
        print(f"🔄 {self.name}: Fallback action: {fallback_action}")
        return fallback_action, fallback_amount, True

    def get_raw_action(self, game_history, legal_actions, amount_to_call, error_message: str = "") -> tuple[str, int]:
        """
        Get raw action from player. This should be overridden by subclasses.
        Base implementation handles scripted actions for testing.
        
        Args:
            game_history: Game history so far
            legal_actions: List of valid actions
            amount_to_call: Amount needed to call
            error_message: Error message from previous attempt (if any)
            
        Returns:
            tuple: (action, amount) - raw response that may need validation
        """
        # Handle scripted actions for testing
        if self.scripted_actions:
            action, amount = self.scripted_actions.pop(0)
            return action, amount
        
        # This should be overridden by subclasses for real players
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_raw_action()")

    def get_action(self, game_history, legal_actions, amount_to_call, debug: bool = False):
        """
        Gets the player's action with validation. This is the main entry point.
        
        Args:
            debug: If True, print detailed debugging information
        
        Returns:
            tuple: (action, amount, is_fallback) - is_fallback=True if this was a fallback action
        """
        return self.get_action_with_validation(game_history, legal_actions, amount_to_call, debug=debug)
    

    def reset_for_new_hand(self):
        """
        Resets the player's state for a new hand.
        """
        self.hand = []
        self.is_folded = False
        self.is_all_in = False
        self.current_bet = 0

    def place_bet(self, amount):
        """
        Places a bet, ensuring the player cannot bet more than their stack.
        """
        bet_amount = min(amount, self.stack)
        self.stack -= bet_amount
        self.current_bet += bet_amount
        if self.stack == 0:
            self.is_all_in = True
        return bet_amount
    
    def get_validation_failure_summary(self) -> dict:
        """
        Get a summary of validation failures for debugging.
        
        Returns:
            dict: Summary of validation patterns and common errors
        """
        if not hasattr(self, '_validation_failures') or not self._validation_failures:
            return {'total_failures': 0, 'common_errors': [], 'patterns': {}}
        
        failures = self._validation_failures
        total_failures = len(failures)
        
        # Analyze error patterns
        error_counts = {}
        action_patterns = {}
        
        for failure in failures:
            for error in failure['errors']:
                error_type = error['error']
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                action = error['action']
                if action != 'EXCEPTION':
                    action_patterns[action] = action_patterns.get(action, 0) + 1
        
        # Sort by frequency
        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_failures': total_failures,
            'total_attempts': sum(len(f['errors']) for f in failures),
            'common_errors': common_errors[:5],  # Top 5 errors
            'action_patterns': action_patterns,
            'recent_failure': failures[-1] if failures else None
        }