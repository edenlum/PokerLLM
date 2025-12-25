"""
Command-line interface for the LLM poker benchmark.
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.runner import BenchmarkRunner
from benchmark.database import BenchmarkDatabase


def cmd_register(args):
    """Register a new LLM for benchmarking."""
    runner = BenchmarkRunner(args.db)
    
    runner.register_llm(
        name=args.name,
        provider=args.provider,
        model=args.model
    )


def cmd_list_llms(args):
    """List all registered LLMs."""
    db = BenchmarkDatabase(args.db)
    llms = db.get_registered_llms()
    
    if not llms:
        print("No LLMs registered yet.")
        return
    
    print(f"\n📋 Registered LLMs ({len(llms)}):")
    print("-" * 60)
    for llm in llms:
        print(f"Name: {llm['name']}")
        print(f"  Provider: {llm['provider']}")
        print(f"  Model: {llm['model']}")
        print(f"  Temperature: {llm['temperature']}")
        print()


def cmd_run_session(args):
    """Run a single heads-up session between two LLMs."""
    runner = BenchmarkRunner(args.db)
    db = BenchmarkDatabase(args.db)
    
    # Get LLM configs
    llms = {llm['name']: llm for llm in db.get_registered_llms()}
    
    if args.llm1 not in llms:
        print(f"❌ LLM '{args.llm1}' not found. Use 'list-llms' to see available LLMs.")
        return
    
    if args.llm2 not in llms:
        print(f"❌ LLM '{args.llm2}' not found. Use 'list-llms' to see available LLMs.")
        return
    
    # Convert to config format
    import json
    
    llm1_config = {
        'name': llms[args.llm1]['name'],
        'provider': llms[args.llm1]['provider'],
        'model': llms[args.llm1]['model'],
        'temperature': llms[args.llm1]['temperature'],
        **json.loads(llms[args.llm1]['config_json'])
    }
    
    llm2_config = {
        'name': llms[args.llm2]['name'],
        'provider': llms[args.llm2]['provider'],
        'model': llms[args.llm2]['model'],
        'temperature': llms[args.llm2]['temperature'],
        **json.loads(llms[args.llm2]['config_json'])
    }
    
    try:
        result = runner.run_heads_up_session(llm1_config, llm2_config, args.hands)
        result_id = db.save_game_result(result)
        print(f"✓ Session completed and saved (ID: {result_id})")
    except Exception as e:
        print(f"❌ Session failed: {e}")


def cmd_run_tournament(args):
    """Run a round-robin tournament between all registered LLMs."""
    runner = BenchmarkRunner(args.db)
    
    # Determine if running in parallel
    parallel = args.parallel and not args.sequential
    
    try:
        if parallel:
            print(f"🚀 Running tournament in parallel mode...")
            results = runner.run_round_robin(args.hands, parallel=True, max_workers=args.workers)
        else:
            print(f"🐌 Running tournament in sequential mode...")
            results = runner.run_round_robin(args.hands, parallel=False)
            
        print(f"\n✓ Tournament completed with {len(results)} sessions!")
        
        # Show leaderboard
        runner.print_leaderboard()
        
    except Exception as e:
        print(f"❌ Tournament failed: {e}")


def cmd_leaderboard(args):
    """Show current leaderboard."""
    runner = BenchmarkRunner(args.db)
    runner.print_leaderboard()


def cmd_results(args):
    """Show detailed results."""
    db = BenchmarkDatabase(args.db)
    
    if args.llm:
        results = db.get_results_for_llm(args.llm)
        print(f"\n📊 Results for {args.llm}:")
    else:
        results = db.get_all_results()
        print("\n📊 All Results:")
    
    if not results:
        print("No results found.")
        return
    
    print("-" * 80)
    for result in results[:args.limit]:
        winnings1_per_hand = result.llm1_winnings / result.hands_played if result.hands_played > 0 else 0
        winnings2_per_hand = result.llm2_winnings / result.hands_played if result.hands_played > 0 else 0
        
        print(f"Date: {result.session_date[:19]}")
        print(f"Match: {result.llm1_name} vs {result.llm2_name}")
        print(f"Hands: {result.hands_played}")
        print(f"Results: {result.llm1_name} {winnings1_per_hand:+.2f}/hand, {result.llm2_name} {winnings2_per_hand:+.2f}/hand")
        
        # Show fallback information if any
        if hasattr(result, 'llm1_fallbacks') and hasattr(result, 'llm2_fallbacks'):
            if result.llm1_fallbacks > 0 or result.llm2_fallbacks > 0:
                print(f"Fallbacks: {result.llm1_name} {result.llm1_fallbacks}, {result.llm2_name} {result.llm2_fallbacks}")
        
        print()


def cmd_generate_site(args):
    """Generate GitHub Pages site from benchmark data."""
    import sys
    import os
    
    # Import site generator
    try:
        from benchmark.site_generator import SiteGenerator
    except ImportError:
        # Try relative import
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from benchmark.site_generator import SiteGenerator
    
    try:
        generator = SiteGenerator(args.db, args.output)
        generator.generate_site()
        
        print(f"\n🌐 Site generated successfully!")
        print(f"📁 Output: {args.output}")
        print(f"🔗 Open {args.output}/index.html in a browser to view the site")
        
    except Exception as e:
        print(f"❌ Site generation failed: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="LLM Poker Benchmark CLI")
    parser.add_argument("--db", default="benchmark/results.db", help="Database path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register LLM command
    register_parser = subparsers.add_parser("register", help="Register a new LLM")
    register_parser.add_argument("name", help="LLM name (e.g., 'gpt-4-turbo')")
    register_parser.add_argument("provider", help="Provider (e.g., 'openai', 'google')")
    register_parser.add_argument("model", help="Model name (e.g., 'gpt-4-turbo', 'gemini-pro')")
    register_parser.add_argument("--temperature", type=float, default=0.7, help="Temperature (default: 0.7)")
    register_parser.add_argument("--api-key", help="API key (optional, can use env vars)")
    register_parser.set_defaults(func=cmd_register)
    
    # List LLMs command
    list_parser = subparsers.add_parser("list-llms", help="List registered LLMs")
    list_parser.set_defaults(func=cmd_list_llms)
    
    # Run session command
    session_parser = subparsers.add_parser("run-session", help="Run heads-up session")
    session_parser.add_argument("llm1", help="First LLM name")
    session_parser.add_argument("llm2", help="Second LLM name")
    session_parser.add_argument("--hands", type=int, default=1000, help="Max hands (default: 1000)")
    session_parser.set_defaults(func=cmd_run_session)
    
    # Run tournament command
    tournament_parser = subparsers.add_parser("run-tournament", help="Run round-robin tournament")
    tournament_parser.add_argument("--hands", type=int, default=1000, help="Max hands per session (default: 1000)")
    tournament_parser.add_argument("--parallel", action="store_true", default=True, help="Run sessions in parallel (default: True)")
    tournament_parser.add_argument("--sequential", action="store_true", help="Run sessions sequentially (overrides --parallel)")
    tournament_parser.add_argument("--workers", type=int, help="Number of parallel workers (default: auto)")
    tournament_parser.set_defaults(func=cmd_run_tournament)
    
    # Leaderboard command
    leaderboard_parser = subparsers.add_parser("leaderboard", help="Show leaderboard")
    leaderboard_parser.set_defaults(func=cmd_leaderboard)
    
    # Results command
    results_parser = subparsers.add_parser("results", help="Show detailed results")
    results_parser.add_argument("--llm", help="Show results for specific LLM")
    results_parser.add_argument("--limit", type=int, default=10, help="Limit number of results (default: 10)")
    results_parser.set_defaults(func=cmd_results)
    
    # Generate site command
    site_parser = subparsers.add_parser("generate-site", help="Generate GitHub Pages site")
    site_parser.add_argument("--output", default="docs", help="Output directory (default: docs)")
    site_parser.set_defaults(func=cmd_generate_site)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
