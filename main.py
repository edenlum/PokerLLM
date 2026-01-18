from simulator.Game import Game
from agents.HumanPlayer import HumanPlayer
from agents.AIPlayer import AIPlayer

def main():
    print("=== Poker Game: You vs OpenAI Bot ===\n")
    
    # Create AI opponent
    # try:
    #     ai_opponent = AIPlayer(
    #         name="GPT-Bot", 
    #         stack=1000, 
    #         provider='google',
    #         model='gemini-2.5-flash',
    #         temperature=0.7
    #     )
    #     print(f"✓ Created AI opponent: {ai_opponent.name}")
    # except Exception as e:
    #     print(f"✗ Failed to create AI opponent: {e}")
    #     print("Make sure you have:")
    #     print("1. Installed dependencies: pip install openai python-dotenv")
    #     print("2. Set API key: export OPENAI_API_KEY='your-key-here'")
    #     return
    
    # Set up game with you vs AI
    players_data = [('You', 1000), ('GPT-Bot', 1000)]
    game = Game(players_data, small_blind=5, big_blind=10)
    
    # Replace with actual player objects
    game.players[0] = HumanPlayer('You', 1000)
    game.players[1] = HumanPlayer('Gal', 1000) # ai_opponent
    
    print(f"\nGame setup:")
    print(f"Players: {[p.name for p in game.players]}")
    print(f"Starting stacks: {[p.stack for p in game.players]}")
    print(f"Blinds: {game.small_blind}/{game.big_blind}")
    print("\nLet's play poker! 🃏\n")
    
    # Game loop
    hand_count = 0
    while True:
        hand_count += 1
        print(f"=== Hand #{hand_count} ===")
        
        try:
            game.run_hand()
        except Exception as e:
            print(f"Error during hand: {e}")
            break
        
        # Check if anyone is out of chips
        active_players = [p for p in game.players if p.stack > 0]
        if len(active_players) < 2:
            print(f"\n🎉 Game Over! Winner: {active_players[0].name if active_players else 'No one'}")
            break
        
        print(f"\nCurrent stacks:")
        for player in game.players:
            print(f"  {player.name}: {player.stack} chips")
        
        print("\n" + "="*50)
        play_again = input("Play another hand? (y/n): ").lower().strip()
        if play_again != 'y':
            break
    
    print("\nThanks for playing! 🎲")

if __name__ == "__main__":
    main()


