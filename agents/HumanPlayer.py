from .Player import Player

class HumanPlayer(Player):
    def get_raw_action(self, game_history: str, legal_actions: list[str], amount_to_call: int, error_message: str = "") -> tuple[str, int]:
        """
        Gets the human player's raw action input. Returns (action, amount) tuple.
        Validation is handled by the parent class.
        """
        print(f"\nYour turn, {self.name}.")
        print(f"Your hand: {self.hand}")
        print(f"Your stack: {self.stack}")
        print(f"Amount to call: {amount_to_call}")
        print(f"Legal actions: {legal_actions}")
        
        # Show error message from previous attempt if any
        if error_message:
            print(f"❌ {error_message}")
            print("Please try again:")

        def parse_human_input(action_str: str) -> tuple[str, int]:
            """Parse human input string into action and amount."""
            parts = action_str.lower().strip().split()
            
            if not parts:
                raise ValueError("No action provided.")
            
            action = parts[0]
            
            # Parse amount for bet/raise actions
            if action in ['bet', 'raise']:
                if len(parts) != 2:
                    raise ValueError(f"Expected format: '{action} <amount>' (e.g., '{action} 50')")
                try:
                    amount = int(parts[1])
                except ValueError:
                    raise ValueError("Amount must be a number.")
            else:
                amount = 0
            
            return action, amount

        # Get input from human (no validation here, just parsing)
        while True:
            try:
                action_str = input("Enter your action (e.g., 'call', 'raise 50', 'fold'): ")
                action, amount = parse_human_input(action_str)
                return action, amount
                
            except ValueError as e:
                print(f"❌ Input error: {e}")
                print("Please try again:")
            except KeyboardInterrupt:
                print("\nGame interrupted by user.")
                return 'fold', 0
