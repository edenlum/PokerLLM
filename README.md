# PokerLLM: A Poker Bot Powered by Large Language Models

This project aims to develop a powerful poker bot by leveraging the capabilities of Large Language Models (LLMs). The core of the project is a text-based poker simulator where LLM-powered agents can play against each other. The strength of an agent is measured by its winnings, providing a clear metric for evaluating different approaches.

## How it Works

The poker game is simulated in a text-based environment. The game state, including actions like drawing cards, betting, and folding, is represented as text. LLM agents participate in the game by generating text that corresponds to their chosen actions.

For example, a round of the game might look like this:

```
--- New Hand ---
Player 1 (you): [Ah, Kd]
Player 2: [?, ?]

--- Pre-flop ---
Player 2 bets 10
Player 1 (you): ?
```

The LLM agent's task is to choose the next token, which represents its action (e.g., "call", "raise 20", "fold").

## Project Structure

- `simulator/`: Contains the core poker simulation logic, including card, deck, game, and hand evaluation.
- `agents/`: Contains different player implementations, such as the `HumanPlayer` for interactive play and future AI agents.
- `tests/`: Contains unit tests for both the simulator and agent components.
- `main.py`: The entry point for running the poker simulation.

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/PokerLLM.git
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the simulator (interactive mode):**
    ```bash
    python3 main.py
    ```
    Follow the prompts in the terminal to play as a human player.

## Agent Development

The primary focus of this project is to experiment with different techniques for improving the poker agents. Some of the methods we are exploring include:

*   **Fine-tuning:** We are fine-tuning existing LLMs on a dataset of poker games to teach them the nuances of the game.
*   **Prompt Engineering:** We are experimenting with different prompts to guide the LLM's decision-making process.
*   **Reasoning:** We are developing techniques to enable the LLM to reason about the game state and make more strategic decisions.

## Contributing

We welcome contributions from the community. If you have an idea for a new agent or a way to improve the simulator, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.