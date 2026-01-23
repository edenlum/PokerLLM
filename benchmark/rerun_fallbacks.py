#!/usr/bin/env python3
"""
Script to rerun benchmark sessions that had fallback actions.
This allows you to fix issues and rerun only the problematic sessions.
"""

import json
import sqlite3
import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.database import BenchmarkDatabase, GameResult
from benchmark.runner import BenchmarkRunner


def get_sessions_with_fallbacks(db_path: str, min_fallbacks: int = 1) -> List[Dict]:
    """
    Get all sessions that had fallback actions.
    
    Args:
        db_path: Path to the database
        min_fallbacks: Minimum number of fallbacks to include (default: 1)
    
    Returns:
        List of session dictionaries with fallback info
    """
    db = BenchmarkDatabase(db_path)
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT id, llm1_name, llm2_name, llm1_winnings, llm2_winnings,
                   hands_played, session_date, llm1_config, llm2_config,
                   COALESCE(llm1_fallbacks, 0) as llm1_fallbacks,
                   COALESCE(llm2_fallbacks, 0) as llm2_fallbacks
            FROM game_results
            WHERE COALESCE(llm1_fallbacks, 0) >= ? OR COALESCE(llm2_fallbacks, 0) >= ?
            ORDER BY (COALESCE(llm1_fallbacks, 0) + COALESCE(llm2_fallbacks, 0)) DESC
        """, (min_fallbacks, min_fallbacks))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row['id'],
                'llm1_name': row['llm1_name'],
                'llm2_name': row['llm2_name'],
                'llm1_fallbacks': row['llm1_fallbacks'],
                'llm2_fallbacks': row['llm2_fallbacks'],
                'total_fallbacks': row['llm1_fallbacks'] + row['llm2_fallbacks'],
                'hands_played': row['hands_played'],
                'session_date': row['session_date'],
                'llm1_config': row['llm1_config'],
                'llm2_config': row['llm2_config']
            })
        
        return sessions


def parse_llm_config(config_json: str, llm_name: str, registered_llms: Dict) -> Dict:
    """
    Parse LLM config from JSON and merge with registered LLM info.
    
    Args:
        config_json: JSON string with config
        llm_name: Name of the LLM
        registered_llms: Dict mapping LLM names to their registered configs
    
    Returns:
        Complete LLM config dict
    """
    try:
        config = json.loads(config_json) if config_json else {}
    except:
        config = {}
    
    # Get registered LLM info
    registered = registered_llms.get(llm_name, {})
    
    # Merge: registered info takes precedence, then config JSON
    llm_config = {
        'name': llm_name,
        'provider': registered.get('provider', config.get('provider', '')),
        'model': registered.get('model', config.get('model', '')),
        **config  # Override with any config JSON values
    }
    
    return llm_config


def delete_session_and_logs(db_path: str, session_id: int):
    """Delete a session and its associated hand logs."""
    with sqlite3.connect(db_path) as conn:
        # Delete hand logs first (foreign key constraint)
        conn.execute("DELETE FROM hand_logs WHERE session_id = ?", (session_id,))
        # Delete the session
        conn.execute("DELETE FROM game_results WHERE id = ?", (session_id,))
        conn.commit()
        print(f"  ✓ Deleted session {session_id} and associated hand logs")


def rerun_fallback_sessions(
    db_path: str = "benchmark/results.db",
    min_fallbacks: int = 1,
    max_hands: int = None,
    delete_old: bool = True,
    dry_run: bool = False,
    session_id: int = None
):
    """
    Rerun all sessions that had fallback actions.
    
    Args:
        db_path: Path to the database
        min_fallbacks: Minimum number of fallbacks to rerun (default: 1)
        max_hands: Maximum hands per session (None = use original count)
        delete_old: Whether to delete old sessions after rerunning (default: True)
        dry_run: If True, only show what would be rerun without actually running
        session_id: Optional session ID to rerun only a specific session
    """
    print("🔍 Finding sessions with fallbacks...")
    
    # Get sessions with fallbacks
    if session_id:
        # Get specific session
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, llm1_name, llm2_name, llm1_winnings, llm2_winnings,
                       hands_played, session_date, llm1_config, llm2_config,
                       COALESCE(llm1_fallbacks, 0) as llm1_fallbacks,
                       COALESCE(llm2_fallbacks, 0) as llm2_fallbacks
                FROM game_results
                WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if not row:
                print(f"❌ Session {session_id} not found!")
                return
            sessions = [{
                'id': row['id'],
                'llm1_name': row['llm1_name'],
                'llm2_name': row['llm2_name'],
                'llm1_fallbacks': row['llm1_fallbacks'],
                'llm2_fallbacks': row['llm2_fallbacks'],
                'total_fallbacks': row['llm1_fallbacks'] + row['llm2_fallbacks'],
                'hands_played': row['hands_played'],
                'session_date': row['session_date'],
                'llm1_config': row['llm1_config'],
                'llm2_config': row['llm2_config']
            }]
            if sessions[0]['total_fallbacks'] < min_fallbacks:
                print(f"⚠️  Session {session_id} has {sessions[0]['total_fallbacks']} fallbacks, "
                      f"which is less than --min-fallbacks={min_fallbacks}")
                print(f"   Proceeding anyway since --session-id was specified...")
    else:
        sessions = get_sessions_with_fallbacks(db_path, min_fallbacks)
    
    if not sessions:
        print("✅ No sessions with fallbacks found!")
        return
    
    print(f"\n📊 Found {len(sessions)} sessions with fallbacks:")
    print("=" * 80)
    
    total_fallbacks = 0
    for session in sessions:
        total_fallbacks += session['total_fallbacks']
        print(f"Session {session['id']}: {session['llm1_name']} vs {session['llm2_name']}")
        print(f"  Fallbacks: LLM1={session['llm1_fallbacks']}, LLM2={session['llm2_fallbacks']} (Total: {session['total_fallbacks']})")
        print(f"  Hands: {session['hands_played']}, Date: {session['session_date']}")
        print()
    
    print(f"Total fallbacks across all sessions: {total_fallbacks}")
    
    if dry_run:
        print("\n🔍 DRY RUN: Would rerun these sessions")
        return
    
    # Get registered LLMs
    db = BenchmarkDatabase(db_path)
    registered_llms = {llm['name']: llm for llm in db.get_registered_llms()}
    
    # Initialize runner
    runner = BenchmarkRunner(db_path)
    
    print(f"\n🔄 Rerunning {len(sessions)} sessions...")
    print("=" * 80)
    
    rerun_count = 0
    success_count = 0
    failed_sessions = []
    
    for session in sessions:
        session_id = session['id']
        llm1_name = session['llm1_name']
        llm2_name = session['llm2_name']
        original_hands = session['hands_played']
        
        print(f"\n[{rerun_count + 1}/{len(sessions)}] Rerunning: {llm1_name} vs {llm2_name}")
        print(f"  Original: {original_hands} hands, {session['total_fallbacks']} fallbacks")
        
        try:
            # Parse LLM configs
            llm1_config = parse_llm_config(session['llm1_config'], llm1_name, registered_llms)
            llm2_config = parse_llm_config(session['llm2_config'], llm2_name, registered_llms)
            
            # Check if we have provider/model info
            if not llm1_config.get('provider') or not llm1_config.get('model'):
                print(f"  ⚠️  Skipping: Missing provider/model info for {llm1_name}")
                failed_sessions.append((session_id, llm1_name, llm2_name, "Missing config"))
                continue
            
            if not llm2_config.get('provider') or not llm2_config.get('model'):
                print(f"  ⚠️  Skipping: Missing provider/model info for {llm2_name}")
                failed_sessions.append((session_id, llm1_name, llm2_name, "Missing config"))
                continue
            
            # Determine number of hands to play
            # Note: original_hands represents unique hands, but each hand is played twice internally
            # (with swapped positions), so we divide by 2 to get the correct max_hands value
            if max_hands is not None:
                hands_to_play = max_hands
            else:
                hands_to_play = original_hands // 2
            
            # IMPORTANT: Delete old session BEFORE creating new one to avoid double-counting
            # This ensures the leaderboard doesn't count both sessions
            if delete_old:
                print(f"  🗑️  Deleting old session {session_id} before rerun...")
                delete_session_and_logs(db_path, session_id)
            
            # Rerun the session (this will create a NEW session with a new ID)
            result = runner.run_heads_up_session(
                llm1_config=llm1_config,
                llm2_config=llm2_config,
                max_hands=hands_to_play
            )
            
            # Get the new session ID
            new_session_id = None
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                new_session = conn.execute("""
                    SELECT id FROM game_results 
                    WHERE llm1_name = ? AND llm2_name = ? 
                    AND session_date = ?
                    ORDER BY id DESC LIMIT 1
                """, (llm1_name, llm2_name, result.session_date)).fetchone()
                if new_session:
                    new_session_id = new_session['id']
            
            # Check if fallbacks were reduced
            new_fallbacks = result.llm1_fallbacks + result.llm2_fallbacks
            old_fallbacks = session['total_fallbacks']
            
            if new_fallbacks < old_fallbacks:
                print(f"  ✅ Success! Fallbacks reduced: {old_fallbacks} → {new_fallbacks}")
                if new_session_id:
                    print(f"  📝 New session ID: {new_session_id} (replaced {session_id})")
            elif new_fallbacks == 0:
                print(f"  ✅ Success! No fallbacks!")
                if new_session_id:
                    print(f"  📝 New session ID: {new_session_id} (replaced {session_id})")
            else:
                print(f"  ⚠️  Fallbacks: {old_fallbacks} → {new_fallbacks}")
                if new_session_id:
                    print(f"  📝 New session ID: {new_session_id} (replaced {session_id})")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed_sessions.append((session_id, llm1_name, llm2_name, str(e)))
        
        rerun_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Rerun Summary")
    print("=" * 80)
    print(f"Total sessions: {len(sessions)}")
    print(f"Successfully rerun: {success_count}")
    print(f"Failed: {len(failed_sessions)}")
    
    if failed_sessions:
        print("\n❌ Failed sessions:")
        for session_id, llm1, llm2, error in failed_sessions:
            print(f"  Session {session_id}: {llm1} vs {llm2} - {error}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Rerun benchmark sessions that had fallback actions'
    )
    parser.add_argument(
        '--db',
        default='benchmark/results.db',
        help='Path to benchmark database'
    )
    parser.add_argument(
        '--min-fallbacks',
        type=int,
        default=1,
        help='Minimum number of fallbacks to rerun (default: 1)'
    )
    parser.add_argument(
        '--max-hands',
        type=int,
        default=None,
        help='Maximum hands per session (default: use original count)'
    )
    parser.add_argument(
        '--keep-old',
        action='store_true',
        help='Keep old sessions instead of deleting them'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be rerun without actually running'
    )
    parser.add_argument(
        '--session-id',
        type=int,
        default=None,
        help='Rerun only this specific session ID'
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"❌ Database not found: {args.db}")
        sys.exit(1)
    
    # Run the rerun
    rerun_fallback_sessions(
        db_path=args.db,
        min_fallbacks=args.min_fallbacks,
        max_hands=args.max_hands,
        delete_old=not args.keep_old,
        dry_run=args.dry_run,
        session_id=args.session_id
    )


if __name__ == '__main__':
    main()
