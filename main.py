from simulator.Game import Game
from agents.HumanPlayer import HumanPlayer

if __name__ == "__main__":
    players_data = [('Alice', 1000), ('Bob', 1000)]
    game = Game(players_data)
    game.players[0] = HumanPlayer('You', 1000)

    while True:
        game.run_hand()
        print("\n---")
        play_again = input("Play another hand? (y/n): ").lower().strip()
        if play_again != 'y':
            break


