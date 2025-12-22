from simulator.Card import Card
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

    class PokerResponse(BaseModel):
        action: Literal["check", "call", "raise", "fold", "bet"] = Field(..., description="The action to take")
        amount: int = Field(0, description="The amount to bet or raise", ge=0)

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
                return f"Cannot bet when there's already a bet to call. Use 'raise' instead."
        
        elif action in ['call', 'check', 'fold']:
            # These actions should have amount = 0
            if amount != 0:
                return f"Action '{action}' should not have an amount"
        
        return ""  # Valid action

    def get_action_with_validation(self, game_history, legal_actions, amount_to_call, error_message: str = "") -> tuple[str, int]:
        """
        Get player action with validation and retry logic.
        This calls the subclass's get_raw_action method and validates the result.
        """
        max_attempts = 5
        
        for attempt in range(max_attempts):
            # Get raw action from subclass
            action, amount = self.get_raw_action(game_history, legal_actions, amount_to_call, error_message)
            
            # Validate the action
            error_message = self.validate_action(action, amount, legal_actions, amount_to_call)
            
            if not error_message:
                # Valid action, return it
                return action, amount
            
            # Invalid action, will retry with error message
            if attempt == max_attempts - 1:
                # Last attempt failed, raise error
                raise ValueError(f"❌ {self.name}: Too many invalid attempts ({max_attempts})")
        
        # Should never reach here, but just in case
        raise ValueError(f"❌ {self.name}: Validation failed after {max_attempts} attempts")

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

    def get_action(self, game_history, legal_actions, amount_to_call):
        """
        Gets the player's action with validation. This is the main entry point.
        """
        return self.get_action_with_validation(game_history, legal_actions, amount_to_call)
    

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
