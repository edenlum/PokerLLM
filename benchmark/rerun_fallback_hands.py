#!/usr/bin/env python3
"""
Script to rerun only the specific hands that had fallback actions.
This allows you to fix issues and rerun only the problematic hands without rerunning entire sessions.
"""

import json
import sqlite3
import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.database import BenchmarkDatabase, GameResult, HandLog
from benchmark.runner import BenchmarkRunner
from agents.AIPlayer import AIPlayer
from simulator.Game import Game
from benchmark.hand_logger import HandLogger


def get_hands_with_fallbacks(db_path: str, session_id: Optional[int] = None) -> List[Dict]:
    """
    Get all hands that had fallback actions.
    
    Args:
        db_path: Path to the database
        session_id: Optional session ID to filter by
    
    Returns:
        List of hand dictionaries with fallback info
    """
    db = BenchmarkDatabase(db_path)
    
    query = """
        SELECT hl.*, gr.llm1_config, gr.llm2_config, gr.hands_played as session_hands
        FROM hand_logs hl
        JOIN game_results gr ON hl.session_id = gr.id
    """
    
    params = []
    if session_id:
        query += " WHERE hl.session_id = ?"
        params.append(session_id)
    
    query += " ORDER BY hl.session_id, hl.hand_number"
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query, params)
        
        hands = []
        for row in cursor.fetchall():
            # Parse actions to count fallbacks
            try:
                actions = json.loads(row['actions'])
                fallback_count = sum(1 for a in actions if a.get('is_fallback', False))
                llm1_fallbacks = sum(1 for a in actions 
                                    if a.get('is_fallback', False) and a.get('player') == row['llm1_name'])
                llm2_fallbacks = sum(1 for a in actions 
                                    if a.get('is_fallback', False) and a.get('player') == row['llm2_name'])
            except:
                fallback_count = 0
                llm1_fallbacks = 0
                llm2_fallbacks = 0
            
            if fallback_count > 0:
                hands.append({
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'hand_number': row['hand_number'],
                    'llm1_name': row['llm1_name'],
                    'llm2_name': row['llm2_name'],
                    'llm1_fallbacks': llm1_fallbacks,
                    'llm2_fallbacks': llm2_fallbacks,
                    'total_fallbacks': fallback_count,
                    'llm1_config': row['llm1_config'],
                    'llm2_config': row['llm2_config'],
                    'hand_date': row['hand_date'],
                    'session_hands': row['session_hands']
                })
        
        return hands


def rerun_single_hand(
    db_path: str,
    hand_log: HandLog,
    llm1_config: Dict,
    llm2_config: Dict,
    initial_stack1: int,
    initial_stack2: int,
    hand_seed: int
) -> Dict:
    """
    Rerun a single hand with the same seed and initial conditions.
    
    Returns:
        Dict with new hand results
    """
    # Create AI players
    player1 = AIPlayer(
        name=llm1_config['name'],
        stack=initial_stack1,
        provider=llm1_config['provider'],
        model=llm1_config.get('model')
    )
    
    player2 = AIPlayer(
        name=llm2_config['name'],
        stack=initial_stack2,
        provider=llm2_config['provider'],
        model=llm2_config.get('model')
    )
    
    # Create game
    players_data = [(player1.name, initial_stack1), (player2.name, initial_stack2)]
    game = Game(players_data, small_blind=50, big_blind=100)
    game.players[0] = player1
    game.players[1] = player2
    
    # Create hand logger
    hand_logger = HandLogger(game)
    
    # Save stacks before hand
    stack_before_p1 = player1.stack
    stack_before_p2 = player2.stack
    
    # Run the hand with the same seed
    game.run_hand(seed=hand_seed)
    
    # Calculate winnings
    winnings1 = player1.stack - stack_before_p1
    winnings2 = player2.stack - stack_before_p2
    
    # Count fallbacks
    fallback_count1 = 0
    fallback_count2 = 0
    if hasattr(game, 'fallback_actions'):
        for fallback in game.fallback_actions:
            if fallback['player'] == player1.name:
                fallback_count1 += 1
            elif fallback['player'] == player2.name:
                fallback_count2 += 1
    
    # Get hand log
    hand_data = hand_logger.get_last_hand()
    
    return {
        'winnings1': winnings1,
        'winnings2': winnings2,
        'fallback_count1': fallback_count1,
        'fallback_count2': fallback_count2,
        'hand_data': hand_data,
        'final_stack1': player1.stack,
        'final_stack2': player2.stack
    }


def update_hand_log(db_path: str, hand_log_id: int, new_hand_data: Dict, session_id: int, hand_number: int):
    """Update a hand log in the database."""
    # Convert hand data to database format
    players = new_hand_data['players']
    player1, player2 = players[0], players[1]
    
    winners = new_hand_data.get('winners', [])
    if len(winners) == 1:
        if winners[0] == player1:
            winner = 'llm1'
        elif winners[0] == player2:
            winner = 'llm2'
        else:
            winner = 'unknown'
    elif len(winners) > 1:
        winner = 'split'
    else:
        winner = 'none'
    
    hand_strengths = new_hand_data.get('hand_strengths', {})
    strength1 = hand_strengths.get(player1, {})
    strength2 = hand_strengths.get(player2, {})
    
    if isinstance(strength1, dict):
        strength1 = strength1.get('strength', 'unknown')
    if isinstance(strength2, dict):
        strength2 = strength2.get('strength', 'unknown')
    
    # Update hand_date to current time so it appears as recently updated
    new_hand_date = datetime.now().isoformat()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            UPDATE hand_logs
            SET llm1_hole_cards = ?,
                llm2_hole_cards = ?,
                community_cards = ?,
                actions = ?,
                pot_size = ?,
                winner = ?,
                llm1_winnings = ?,
                llm2_winnings = ?,
                showdown = ?,
                hand_strength_llm1 = ?,
                hand_strength_llm2 = ?,
                hand_date = ?
            WHERE id = ?
        """, (
            json.dumps(new_hand_data['hole_cards'].get(player1, [])),
            json.dumps(new_hand_data['hole_cards'].get(player2, [])),
            json.dumps(new_hand_data['community_cards']),
            json.dumps(new_hand_data['actions']),
            new_hand_data['final_pot'],
            winner,
            new_hand_data['winnings'].get(player1, 0.0),
            new_hand_data['winnings'].get(player2, 0.0),
            new_hand_data['showdown'],
            strength1,
            strength2,
            new_hand_date,
            hand_log_id
        ))
        conn.commit()
        
        # Verify the update
        if cursor.rowcount == 0:
            raise ValueError(f"Failed to update hand log {hand_log_id} - no rows affected")


def recalculate_session_totals(db_path: str, session_id: int):
    """Recalculate session totals from hand logs."""
    db = BenchmarkDatabase(db_path)
    hand_logs = db.get_hand_logs(session_id=session_id, limit=10000)
    
    # Get session info
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        session_row = conn.execute(
            "SELECT * FROM game_results WHERE id = ?", (session_id,)
        ).fetchone()
        
        if not session_row:
            return
        
        llm1_name = session_row['llm1_name']
        llm2_name = session_row['llm2_name']
        
        # Calculate totals
        total_winnings1 = 0
        total_winnings2 = 0
        total_fallbacks1 = 0
        total_fallbacks2 = 0
        
        for hand_log in hand_logs:
            total_winnings1 += hand_log.llm1_winnings
            total_winnings2 += hand_log.llm2_winnings
            
            # Count fallbacks from actions
            try:
                actions = json.loads(hand_log.actions)
                for action in actions:
                    if action.get('is_fallback', False):
                        if action.get('player') == llm1_name:
                            total_fallbacks1 += 1
                        elif action.get('player') == llm2_name:
                            total_fallbacks2 += 1
            except:
                pass
        
        # Update session
        conn.execute("""
            UPDATE game_results
            SET llm1_winnings = ?,
                llm2_winnings = ?,
                llm1_fallbacks = ?,
                llm2_fallbacks = ?,
                hands_played = ?
            WHERE id = ?
        """, (
            total_winnings1,
            total_winnings2,
            total_fallbacks1,
            total_fallbacks2,
            len(hand_logs),
            session_id
        ))
        conn.commit()


def rerun_fallback_hands(
    db_path: str = "benchmark/results.db",
    session_id: Optional[int] = None,
    dry_run: bool = False
):
    """
    Rerun only the hands that had fallback actions.
    
    Args:
        db_path: Path to the database
        session_id: Optional session ID to limit reruns to one session
        dry_run: If True, only show what would be rerun
    """
    print("🔍 Finding hands with fallbacks...")
    
    # Get hands with fallbacks
    hands = get_hands_with_fallbacks(db_path, session_id)
    
    if not hands:
        print("✅ No hands with fallbacks found!")
        return
    
    # Group by session
    sessions = {}
    for hand in hands:
        sid = hand['session_id']
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append(hand)
    
    print(f"\n📊 Found {len(hands)} hands with fallbacks across {len(sessions)} sessions:")
    print("=" * 80)
    
    for sid, session_hands in sessions.items():
        total_fallbacks = sum(h['total_fallbacks'] for h in session_hands)
        print(f"Session {sid}: {len(session_hands)} hands, {total_fallbacks} total fallbacks")
        for hand in session_hands:
            print(f"  Hand {hand['hand_number']}: {hand['llm1_name']} vs {hand['llm2_name']} "
                  f"({hand['total_fallbacks']} fallbacks)")
    
    if dry_run:
        print("\n🔍 DRY RUN: Would rerun these hands")
        return
    
    # Get registered LLMs
    db = BenchmarkDatabase(db_path)
    registered_llms = {llm['name']: llm for llm in db.get_registered_llms()}
    
    print(f"\n🔄 Rerunning {len(hands)} hands...")
    print("=" * 80)
    
    rerun_count = 0
    success_count = 0
    failed_hands = []
    
    # Process by session to track initial stacks
    for sid, session_hands in sessions.items():
        print(f"\n📦 Processing session {sid} ({len(session_hands)} hands)")
        
        # Get session info
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            session_row = conn.execute(
                "SELECT * FROM game_results WHERE id = ?", (sid,)
            ).fetchone()
            
            if not session_row:
                print(f"  ⚠️  Session {sid} not found, skipping")
                continue
            
            # Parse configs
            llm1_config = parse_llm_config(session_row['llm1_config'], session_row['llm1_name'], registered_llms)
            llm2_config = parse_llm_config(session_row['llm2_config'], session_row['llm2_name'], registered_llms)
            
            if not llm1_config.get('provider') or not llm1_config.get('model'):
                print(f"  ⚠️  Skipping: Missing config for {session_row['llm1_name']}")
                continue
            
            if not llm2_config.get('provider') or not llm2_config.get('model'):
                print(f"  ⚠️  Skipping: Missing config for {session_row['llm2_name']}")
                continue
        
        # Get all hand logs for this session to track stack progression
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, hand_number, llm1_winnings, llm2_winnings
                FROM hand_logs
                WHERE session_id = ?
                ORDER BY hand_number ASC
            """, (sid,))
            
            hand_logs_by_number = {}
            hand_log_ids_by_number = {}
            for row in cursor.fetchall():
                hand_logs_by_number[row['hand_number']] = {
                    'llm1_winnings': row['llm1_winnings'],
                    'llm2_winnings': row['llm2_winnings']
                }
                hand_log_ids_by_number[row['hand_number']] = row['id']
        
        # Get full hand log objects for the hands we need to rerun
        all_hand_logs = db.get_hand_logs(session_id=sid, limit=10000)
        hand_log_objects = {hl.hand_number: hl for hl in all_hand_logs}
        
        # Calculate initial stacks (assuming 10000 starting stack)
        initial_stack = 10000
        
        # Process each hand with fallbacks
        for hand_info in session_hands:
            hand_num = hand_info['hand_number']
            hand_log = hand_log_objects.get(hand_num)
            hand_log_id = hand_log_ids_by_number.get(hand_num)
            
            if not hand_log or not hand_log_id:
                print(f"  ⚠️  Hand {hand_num} log not found, skipping")
                continue
            
            print(f"\n  [{rerun_count + 1}/{len(hands)}] Rerunning hand {hand_num}")
            print(f"    Original: {hand_info['total_fallbacks']} fallbacks")
            
            try:
                # Calculate stacks before this hand
                # Sum winnings from all previous hands
                stack1 = initial_stack
                stack2 = initial_stack
                for prev_num in range(1, hand_num):
                    prev_data = hand_logs_by_number.get(prev_num)
                    if prev_data:
                        stack1 += prev_data['llm1_winnings']
                        stack2 += prev_data['llm2_winnings']
                
                # Rerun the hand
                result = rerun_single_hand(
                    db_path=db_path,
                    hand_log=hand_log,
                    llm1_config=llm1_config,
                    llm2_config=llm2_config,
                    initial_stack1=stack1,
                    initial_stack2=stack2,
                    hand_seed=hand_num - 1  # hand_number is 1-indexed, seed is 0-indexed
                )
                
                # Update hand log
                update_hand_log(
                    db_path=db_path,
                    hand_log_id=hand_log_id,
                    new_hand_data=result['hand_data'],
                    session_id=sid,
                    hand_number=hand_num
                )
                
                # Verify the update by reading it back immediately
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    updated_row = conn.execute(
                        "SELECT actions, llm1_winnings, llm2_winnings, hand_date FROM hand_logs WHERE id = ?",
                        (hand_log_id,)
                    ).fetchone()
                    
                    if updated_row:
                        try:
                            updated_actions = json.loads(updated_row['actions'])
                            updated_fallbacks = sum(1 for a in updated_actions if a.get('is_fallback', False))
                            print(f"    📝 DB verified: {updated_fallbacks} fallbacks, "
                                  f"winnings: {updated_row['llm1_winnings']:.2f}/{updated_row['llm2_winnings']:.2f}")
                            
                            # Compare with what we expect
                            if updated_fallbacks != (result['fallback_count1'] + result['fallback_count2']):
                                print(f"    ⚠️  WARNING: Fallback count mismatch! Expected {result['fallback_count1'] + result['fallback_count2']}, got {updated_fallbacks}")
                        except Exception as e:
                            print(f"    ⚠️  Could not verify update: {e}")
                    else:
                        print(f"    ❌ ERROR: Could not read back updated hand log!")
                
                # Check improvement
                old_fallbacks = hand_info['total_fallbacks']
                new_fallbacks = result['fallback_count1'] + result['fallback_count2']
                
                if new_fallbacks < old_fallbacks:
                    print(f"    ✅ Fallbacks reduced: {old_fallbacks} → {new_fallbacks}")
                elif new_fallbacks == 0:
                    print(f"    ✅ No fallbacks!")
                else:
                    print(f"    ⚠️  Fallbacks: {old_fallbacks} → {new_fallbacks}")
                
                success_count += 1
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                import traceback
                traceback.print_exc()
                failed_hands.append((sid, hand_num, str(e)))
            
            rerun_count += 1
        
        # Recalculate session totals
        print(f"\n  📊 Recalculating session {sid} totals...")
        recalculate_session_totals(db_path, sid)
        print(f"  ✅ Session {sid} updated")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Rerun Summary")
    print("=" * 80)
    print(f"Total hands: {len(hands)}")
    print(f"Successfully rerun: {success_count}")
    print(f"Failed: {len(failed_hands)}")
    
    if failed_hands:
        print("\n❌ Failed hands:")
        for sid, hand_num, error in failed_hands:
            print(f"  Session {sid}, Hand {hand_num}: {error}")


def parse_llm_config(config_json: str, llm_name: str, registered_llms: Dict) -> Dict:
    """Parse LLM config from JSON and merge with registered LLM info."""
    try:
        config = json.loads(config_json) if config_json else {}
    except:
        config = {}
    
    registered = registered_llms.get(llm_name, {})
    
    llm_config = {
        'name': llm_name,
        'provider': registered.get('provider', config.get('provider', '')),
        'model': registered.get('model', config.get('model', '')),
        **config
    }
    
    return llm_config


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Rerun only the specific hands that had fallback actions'
    )
    parser.add_argument(
        '--db',
        default='benchmark/results.db',
        help='Path to benchmark database'
    )
    parser.add_argument(
        '--session-id',
        type=int,
        default=None,
        help='Only rerun hands from this session ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be rerun without actually running'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db):
        print(f"❌ Database not found: {args.db}")
        sys.exit(1)
    
    rerun_fallback_hands(
        db_path=args.db,
        session_id=args.session_id,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
