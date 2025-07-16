from simulator.Card import Card

class Player:
    def __init__(self, name, stack):
        self.name = name
        self.stack = stack
        self.hand = []
        self.is_folded = False
        self.is_all_in = False
        self.current_bet = 0
        self.scripted_actions = []

    def get_action(self, legal_actions, amount_to_call):
        """
        Gets the player's action. This method is intended to be overridden by subclasses.
        """
        print(f"{self.name}'s turn.")
        print(f"Hand: {self.hand}")
        print(f"Stack: {self.stack}")
        print(f"Amount to call: {amount_to_call}")
        print(f"Legal actions: {legal_actions}")

        if self.scripted_actions:
            action, amount = self.scripted_actions.pop(0)
            print(f"{self.name} scripted action: {action} {amount}")
            return action, amount

        if 'check' in legal_actions:
            action = 'check'
            amount = 0
            print(f"{self.name} checks.")
        elif 'call' in legal_actions:
            action = 'call'
            amount = 0
            print(f"{self.name} calls.")
        else:
            action = 'fold'
            amount = 0
            print(f"{self.name} folds.")
        
        return action, amount

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
