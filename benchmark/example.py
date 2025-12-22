#!/usr/bin/env python3
"""
Example script demonstrating the LLM poker benchmark system.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.runner import BenchmarkRunner


def main():
    """Run a simple benchmark example."""
    print("🎯 LLM Poker Benchmark Example")
    print("=" * 50)
    
    # Initialize benchmark runner
    runner = BenchmarkRunner("benchmark/example_results.db")
    
    # Register some example LLMs (you'll need API keys for these to work)
    print("\n📋 Registering LLMs...")
    
    try:
        runner.register_llm(
            name="gemini-2.5-flash",
            provider="google",
            model="gemini-2.5-flash",
            temperature=0.7
        )
        
        runner.register_llm(
            name="gemini-2.5-flash-lite",
            provider="google",
            model="gemini-2.5-flash-lite",
            temperature=0.7
        )
        
    except Exception as e:
        print(f"⚠️  LLM registration failed: {e}")
        print("Make sure you have API keys set up!")
        return
    
    # Show registered LLMs
    print("\n📋 Registered LLMs:")
    llms = runner.db.get_registered_llms()
    for llm in llms:
        print(f"  - {llm['name']} ({llm['provider']}/{llm['model']})")
    
    # Run a small tournament (fewer hands for demo)
    print(f"\n🏆 Running mini tournament (100 hands per session)...")
    
    try:
        results = runner.run_round_robin(max_hands_per_session=100)
        
        print(f"\n✅ Tournament completed!")
        print(f"Sessions played: {len(results)}")
        
        # Show leaderboard
        runner.print_leaderboard()
        
    except Exception as e:
        print(f"❌ Tournament failed: {e}")
        print("This is expected if you don't have API keys set up.")
        print("The benchmark system is ready - just add your API keys!")


if __name__ == "__main__":
    main()
