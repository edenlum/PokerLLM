from .Player import Player

class HumanPlayer(Player):
    def get_action(self, legal_actions, amount_to_call):
        """
        Gets the human player's action, with input validation.
        """
        print(f"\nYour turn, {self.name}.")
        print(f"Your hand: {self.hand}")
        print(f"Your stack: {self.stack}")
        print(f"Amount to call: {amount_to_call}")
        print(f"Legal actions: {legal_actions}")

        while True:
            try:
                action_str = input("Enter your action (e.g., 'call', 'raise 50', 'fold'): ").lower().strip()
                parts = action_str.split()
                action = parts[0]

                if action not in legal_actions:
                    print("Invalid action.")
                    continue

                if action in ['bet', 'raise']:
                    if len(parts) < 2:
                        print("Please specify an amount to bet or raise.")
                        continue
                    amount = int(parts[1])
                    if amount < 0:
                        print("You cannot bet a negative amount.")
                        continue
                    if amount > self.stack:
                        print("You cannot bet more than your stack.")
                        continue
                    if action == 'raise' and amount <= amount_to_call:
                        print(f"Raise amount must be greater than {amount_to_call}.")
                        continue
                else:
                    amount = 0

                return action, amount

            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid action and amount.")

