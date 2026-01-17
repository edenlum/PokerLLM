"""
Benchmark runner for heads-up poker games between LLMs.
"""

import json
import random
from datetime import datetime
from typing import List, Tuple, Dict
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from agents.AIPlayer import AIPlayer
from simulator.Game import Game
from benchmark.database import BenchmarkDatabase, GameResult, HandLog
from benchmark.hand_logger import HandLogger


class BenchmarkRunner:
    """Runs benchmark games between LLMs and tracks results."""
    
    def __init__(self, db_path: str = "benchmark/results.db"):
        """Initialize the benchmark runner."""
        self.db = BenchmarkDatabase(db_path)
        self.starting_stack = 10000  # 100 BB with 50/100 blinds
        self.small_blind = 50
        self.big_blind = 100
    
    def register_llm(self, name: str, provider: str, model: str, **kwargs):
        """Register an LLM for benchmarking."""
        config = {
            **kwargs
        }
        
        self.db.register_llm_config(
            name=name,
            provider=provider,
            model=model,
            config_json=json.dumps(config)
        )
        
        print(f"✓ Registered LLM: {name} ({provider}/{model})")
    
    def run_heads_up_session(self, llm1_config: Dict, llm2_config: Dict, 
                           max_hands: int = 100) -> GameResult:
        """
        Run a heads-up session between two LLMs.
        
        Args:
            llm1_config: Configuration for first LLM
            llm2_config: Configuration for second LLM  
            max_hands: Maximum number of hands to play
            
        Returns:
            GameResult with session statistics
        """
        print(f"\n🎯 Starting heads-up session: {llm1_config['name']} vs {llm2_config['name']}")
        
        # Create AI players
        try:
            player1 = AIPlayer(
                name=llm1_config['name'],
                stack=self.starting_stack,
                provider=llm1_config['provider'],
                model=llm1_config.get('model')
            )
            
            player2 = AIPlayer(
                name=llm2_config['name'],
                stack=self.starting_stack,
                provider=llm2_config['provider'],
                model=llm2_config.get('model')
            )
        except Exception as e:
            print(f"❌ Failed to create AI players: {e}")
            raise
        
        # Track session statistics
        hands_played = 0
        initial_stack1 = self.starting_stack
        initial_stack2 = self.starting_stack
        
        # Create game
        players_data = [(player1.name, self.starting_stack), (player2.name, self.starting_stack)]
        game = Game(players_data, small_blind=self.small_blind, big_blind=self.big_blind)
        game.players[0] = player1
        game.players[1] = player2
        
        # Create hand logger to capture detailed hand information
        hand_logger = HandLogger(game)
        
        print(f"Starting stacks: {self.starting_stack} chips each")
        print(f"Blinds: {self.small_blind}/{self.big_blind}")
        print("🔄 Using duplicate hands with swapped players to eliminate card distribution variance")
        
        # Play hands until max_hands or someone busts
        while hands_played < max_hands:
            # Check if anyone is out of chips
            if player1.stack <= 0 or player2.stack <= 0:
                print(f"💥 Session ended - player busted after {hands_played} hands")
                break
            
            # Check if anyone has very low stack (less than 10 BB)
            min_stack = min(player1.stack, player2.stack)
            if min_stack < self.big_blind * 10:
                print(f"⚠️  Low stack detected ({min_stack} chips), continuing...")
            
            try:
                # Play hand twice with same seed (dealer position increment swaps positions automatically)
                hand_seed = random.randint(0, 2**31 - 1)
                
                # Save stacks before first play
                stack_before_p1 = player1.stack
                stack_before_p2 = player2.stack
                
                # First play: normal
                game.run_hand(seed=hand_seed)
                winnings1_first = player1.stack - stack_before_p1
                winnings2_first = player2.stack - stack_before_p2
                
                # Reset stacks for second play
                player1.stack = stack_before_p1
                player2.stack = stack_before_p2
                
                # Second play: same seed (dealer position will increment, swapping positions)
                game.run_hand(seed=hand_seed)
                winnings1_second = player1.stack - stack_before_p1
                winnings2_second = player2.stack - stack_before_p2
                
                # Average the winnings (eliminates card distribution variance)
                player1.stack = stack_before_p1 + (winnings1_first + winnings1_second) / 2
                player2.stack = stack_before_p2 + (winnings2_first + winnings2_second) / 2
                
                hands_played += 1
                
                # Progress update every 50 hands
                if hands_played % 50 == 0:
                    print(f"Hand {hands_played}: {player1.name}={player1.stack:.0f}, {player2.name}={player2.stack:.0f}")
                
            except Exception as e:
                print(f"❌ Error in hand {hands_played + 1}: {e}")
                break
        
        # Calculate final results
        final_stack1 = player1.stack
        final_stack2 = player2.stack
        
        winnings1 = final_stack1 - initial_stack1
        winnings2 = final_stack2 - initial_stack2
        
        # Verify conservation of chips
        total_chips = final_stack1 + final_stack2
        expected_chips = initial_stack1 + initial_stack2
        if abs(total_chips - expected_chips) > 1:  # Allow for rounding
            print(f"⚠️  Chip conservation error: {total_chips} vs {expected_chips}")
        
        # Count fallback actions
        fallback_count1 = 0
        fallback_count2 = 0
        if hasattr(game, 'fallback_actions'):
            for fallback in game.fallback_actions:
                if fallback['player'] == player1.name:
                    fallback_count1 += 1
                elif fallback['player'] == player2.name:
                    fallback_count2 += 1
        
        print(f"\n📊 Session Results ({hands_played} hands):")
        print(f"  {player1.name}: {winnings1:+.1f} chips ({winnings1/hands_played:+.2f} per hand)")
        if fallback_count1 > 0:
            print(f"    ⚠️  {fallback_count1} fallback actions")
        print(f"  {player2.name}: {winnings2:+.1f} chips ({winnings2/hands_played:+.2f} per hand)")
        if fallback_count2 > 0:
            print(f"    ⚠️  {fallback_count2} fallback actions")
        
        # Create result object
        result = GameResult(
            llm1_name=llm1_config['name'],
            llm2_name=llm2_config['name'],
            llm1_winnings=winnings1,
            llm2_winnings=winnings2,
            hands_played=hands_played,
            session_date=datetime.now().isoformat(),
            llm1_config=json.dumps(llm1_config),
            llm2_config=json.dumps(llm2_config),
            llm1_fallbacks=fallback_count1,
            llm2_fallbacks=fallback_count2
        )
        
        # Save result and get session ID
        session_id = self.db.save_game_result(result)
        
        # Save hand logs
        self._save_hand_logs(hand_logger, session_id)
        
        return result
    
    def _save_hand_logs(self, hand_logger: HandLogger, session_id: int):
        """Save hand logs from the hand logger to the database."""
        
        # Convert hand logs to database format
        db_hands = hand_logger.to_database_format(session_id)
        
        # Save each hand to the database
        for hand_data in db_hands:
            hand_log = HandLog(
                session_id=hand_data['session_id'],
                hand_number=hand_data['hand_number'],
                llm1_name=hand_data['llm1_name'],
                llm2_name=hand_data['llm2_name'],
                llm1_hole_cards=hand_data['llm1_hole_cards'],
                llm2_hole_cards=hand_data['llm2_hole_cards'],
                community_cards=hand_data['community_cards'],
                actions=hand_data['actions'],
                pot_size=hand_data['pot_size'],
                winner=hand_data['winner'],
                llm1_winnings=hand_data['llm1_winnings'],
                llm2_winnings=hand_data['llm2_winnings'],
                hand_date=hand_data['hand_date'],
                showdown=hand_data['showdown'],
                hand_strength_llm1=hand_data['hand_strength_llm1'],
                hand_strength_llm2=hand_data['hand_strength_llm2']
            )
            
            self.db.save_hand_log(hand_log)
    
    def run_round_robin(self, max_hands_per_session: int = 100, parallel: bool = True, max_workers: int = None) -> List[GameResult]:
        """
        Run round-robin tournament between all registered LLMs.
        
        Args:
            max_hands_per_session: Maximum hands per heads-up session
            parallel: Whether to run sessions in parallel (default: True)
            max_workers: Maximum number of parallel workers (default: CPU count)
            
        Returns:
            List of all game results
        """
        if parallel:
            return self._run_round_robin_parallel(max_hands_per_session, max_workers)
        else:
            return self._run_round_robin_sequential(max_hands_per_session)
    
    def _run_round_robin_parallel(self, max_hands_per_session: int, max_workers: int = None) -> List[GameResult]:
        """Run round-robin tournament in parallel."""
        llms = self.db.get_registered_llms()
        
        if len(llms) < 2:
            raise ValueError("Need at least 2 LLMs registered for round-robin")
        
        # Determine number of workers
        if max_workers is None:
            max_workers = min(os.cpu_count() or 4, 8)  # Cap at 8 to avoid overwhelming APIs
        
        print(f"\n🏆 Starting parallel round-robin tournament with {len(llms)} LLMs")
        print(f"🚀 Using {max_workers} parallel workers")
        print(f"LLMs: {[llm['name'] for llm in llms]}")
        
        # Generate all unique pairs
        pairs = list(combinations(llms, 2))
        total_sessions = len(pairs)
        
        print(f"📊 Total sessions to run: {total_sessions}")
        
        results = []
        completed_sessions = 0
        
        # Run sessions in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all sessions
            future_to_pair = {}
            for llm1, llm2 in pairs:
                # Convert DB config to dict format
                llm1_config = {
                    'name': llm1['name'],
                    'provider': llm1['provider'],
                    'model': llm1['model'],
                    'temperature': llm1['temperature'],
                    **json.loads(llm1['config_json'])
                }
                
                llm2_config = {
                    'name': llm2['name'],
                    'provider': llm2['provider'],
                    'model': llm2['model'],
                    'temperature': llm2['temperature'],
                    **json.loads(llm2['config_json'])
                }
                
                future = executor.submit(self._run_single_session, llm1_config, llm2_config, max_hands_per_session)
                future_to_pair[future] = (llm1['name'], llm2['name'])
            
            # Collect results as they complete
            for future in as_completed(future_to_pair):
                llm1_name, llm2_name = future_to_pair[future]
                completed_sessions += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    print(f"✅ [{completed_sessions}/{total_sessions}] {llm1_name} vs {llm2_name} completed")
                    
                except Exception as e:
                    print(f"❌ [{completed_sessions}/{total_sessions}] {llm1_name} vs {llm2_name} failed: {e}")
                    continue
        
        print(f"\n🎉 Parallel round-robin completed! {len(results)}/{total_sessions} sessions successful.")
        return results
    
    def _run_round_robin_sequential(self, max_hands_per_session: int) -> List[GameResult]:
        """Run round-robin tournament sequentially (original implementation)."""
        llms = self.db.get_registered_llms()
        
        if len(llms) < 2:
            raise ValueError("Need at least 2 LLMs registered for round-robin")
        
        print(f"\n🏆 Starting sequential round-robin tournament with {len(llms)} LLMs")
        print(f"LLMs: {[llm['name'] for llm in llms]}")
        
        results = []
        total_sessions = len(llms) * (len(llms) - 1) // 2
        session_count = 0
        
        # Generate all unique pairs
        for llm1, llm2 in combinations(llms, 2):
            session_count += 1
            print(f"\n--- Session {session_count}/{total_sessions} ---")
            
            # Convert DB config to dict format
            llm1_config = {
                'name': llm1['name'],
                'provider': llm1['provider'],
                'model': llm1['model'],
                'temperature': llm1['temperature'],
                **json.loads(llm1['config_json'])
            }
            
            llm2_config = {
                'name': llm2['name'],
                'provider': llm2['provider'],
                'model': llm2['model'],
                'temperature': llm2['temperature'],
                **json.loads(llm2['config_json'])
            }
            
            try:
                result = self._run_single_session(llm1_config, llm2_config, max_hands_per_session)
                results.append(result)
                
            except Exception as e:
                print(f"❌ Session failed: {e}")
                continue
        
        print(f"\n🎉 Sequential round-robin completed! {len(results)} sessions played.")
        return results
    
    def _run_single_session(self, llm1_config: Dict, llm2_config: Dict, max_hands_per_session: int) -> GameResult:
        """Run a single heads-up session and save to database."""
        # run_heads_up_session already saves to database
        result = self.run_heads_up_session(llm1_config, llm2_config, max_hands_per_session)
        return result
    
    def get_leaderboard(self) -> List[Tuple[str, float, int, int, float]]:
        """
        Calculate leaderboard based on average winnings per hand.
        
        Returns:
            List of (llm_name, avg_winnings_per_hand, total_hands, num_sessions, fallback_rate)
        """
        all_results = self.db.get_all_results()
        
        # Aggregate results by LLM
        llm_stats = {}
        
        for result in all_results:
            # Add stats for LLM1
            if result.llm1_name not in llm_stats:
                llm_stats[result.llm1_name] = {'total_winnings': 0, 'total_hands': 0, 'sessions': 0, 'total_fallbacks': 0}
            
            llm_stats[result.llm1_name]['total_winnings'] += result.llm1_winnings
            llm_stats[result.llm1_name]['total_hands'] += result.hands_played
            llm_stats[result.llm1_name]['sessions'] += 1
            if hasattr(result, 'llm1_fallbacks'):
                llm_stats[result.llm1_name]['total_fallbacks'] += result.llm1_fallbacks
            
            # Add stats for LLM2
            if result.llm2_name not in llm_stats:
                llm_stats[result.llm2_name] = {'total_winnings': 0, 'total_hands': 0, 'sessions': 0, 'total_fallbacks': 0}
            
            llm_stats[result.llm2_name]['total_winnings'] += result.llm2_winnings
            llm_stats[result.llm2_name]['total_hands'] += result.hands_played
            llm_stats[result.llm2_name]['sessions'] += 1
            if hasattr(result, 'llm2_fallbacks'):
                llm_stats[result.llm2_name]['total_fallbacks'] += result.llm2_fallbacks
        
        # Calculate average winnings per hand and fallback rate
        leaderboard = []
        for llm_name, stats in llm_stats.items():
            if stats['total_hands'] > 0:
                avg_winnings_per_hand = stats['total_winnings'] / stats['total_hands']
                fallback_rate = (stats['total_fallbacks'] / stats['total_hands']) * 100  # Percentage
                leaderboard.append((
                    llm_name,
                    avg_winnings_per_hand,
                    stats['total_hands'],
                    stats['sessions'],
                    fallback_rate
                ))
        
        # Sort by average winnings per hand (descending)
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        
        return leaderboard
    
    def print_leaderboard(self):
        """Print formatted leaderboard."""
        leaderboard = self.get_leaderboard()
        
        if not leaderboard:
            print("No results available yet.")
            return
        
        print("\n🏆 LLM Poker Leaderboard")
        print("=" * 85)
        print(f"{'Rank':<4} {'LLM Name':<20} {'Avg/Hand':<12} {'Total Hands':<12} {'Sessions':<10} {'Fallback%':<8}")
        print("-" * 85)
        
        for rank, (llm_name, avg_per_hand, total_hands, sessions, fallback_rate) in enumerate(leaderboard, 1):
            fallback_str = f"{fallback_rate:.1f}%" if fallback_rate > 0 else "0%"
            print(f"{rank:<4} {llm_name:<20} {avg_per_hand:+8.2f}    {total_hands:<12} {sessions:<10} {fallback_str:<8}")
        
        print("=" * 85)
        print("Note: Avg/Hand = Average chips won per hand across all opponents")
        print("      Fallback% = Percentage of actions that were fallbacks due to validation errors")
