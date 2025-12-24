"""
Database module for storing benchmark results.
"""

import sqlite3
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GameResult:
    """Result of a single heads-up session between two LLMs."""
    llm1_name: str
    llm2_name: str
    llm1_winnings: float  # Total winnings for LLM1 (negative if loss)
    llm2_winnings: float  # Total winnings for LLM2 (negative if loss)
    hands_played: int
    session_date: str
    llm1_config: str  # JSON string with model config (temperature, etc.)
    llm2_config: str
    llm1_fallbacks: int = 0  # Number of fallback actions for LLM1
    llm2_fallbacks: int = 0  # Number of fallback actions for LLM2


@dataclass
class HandLog:
    """Detailed log of a single poker hand."""
    session_id: int  # Foreign key to game_results
    hand_number: int  # Hand number within the session
    llm1_name: str
    llm2_name: str
    llm1_hole_cards: str  # JSON: ["Ah", "Kd"]
    llm2_hole_cards: str  # JSON: ["Qc", "Js"]
    community_cards: str  # JSON: ["Tc", "9h", "8s", "7d", "6c"]
    actions: str  # JSON: [{"player": "llm1", "action": "raise", "amount": 200, "is_fallback": false}, ...]
    pot_size: int
    winner: str  # "llm1", "llm2", or "split"
    llm1_winnings: float  # Winnings for this specific hand
    llm2_winnings: float
    hand_date: str
    showdown: bool  # Whether hand went to showdown
    hand_strength_llm1: str  # Hand ranking (e.g., "pair", "flush")
    hand_strength_llm2: str


class BenchmarkDatabase:
    """Manages the benchmark results database."""
    
    def __init__(self, db_path: str = "benchmark/results.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            # Create main table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    llm1_name TEXT NOT NULL,
                    llm2_name TEXT NOT NULL,
                    llm1_winnings REAL NOT NULL,
                    llm2_winnings REAL NOT NULL,
                    hands_played INTEGER NOT NULL,
                    session_date TEXT NOT NULL,
                    llm1_config TEXT,
                    llm2_config TEXT,
                    llm1_fallbacks INTEGER DEFAULT 0,
                    llm2_fallbacks INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    temperature REAL,
                    config_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_llm_names 
                ON game_results(llm1_name, llm2_name)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_date 
                ON game_results(session_date)
            """)
            
            # Create hand logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hand_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    hand_number INTEGER NOT NULL,
                    llm1_name TEXT NOT NULL,
                    llm2_name TEXT NOT NULL,
                    llm1_hole_cards TEXT,
                    llm2_hole_cards TEXT,
                    community_cards TEXT,
                    actions TEXT,
                    pot_size INTEGER NOT NULL,
                    winner TEXT,
                    llm1_winnings REAL NOT NULL,
                    llm2_winnings REAL NOT NULL,
                    hand_date TEXT NOT NULL,
                    showdown BOOLEAN DEFAULT 0,
                    hand_strength_llm1 TEXT,
                    hand_strength_llm2 TEXT,
                    FOREIGN KEY (session_id) REFERENCES game_results (id)
                )
            """)
            
            # Migrate existing databases to add fallback columns
            self._migrate_database(conn)
    
    def _migrate_database(self, conn):
        """Migrate database schema to add missing columns."""
        # Check if fallback columns exist
        cursor = conn.execute("PRAGMA table_info(game_results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add fallback columns if they don't exist
        if 'llm1_fallbacks' not in columns:
            conn.execute("ALTER TABLE game_results ADD COLUMN llm1_fallbacks INTEGER DEFAULT 0")
            print("Added llm1_fallbacks column to database")
            
        if 'llm2_fallbacks' not in columns:
            conn.execute("ALTER TABLE game_results ADD COLUMN llm2_fallbacks INTEGER DEFAULT 0")
            print("Added llm2_fallbacks column to database")
    
    def save_game_result(self, result: GameResult) -> int:
        """Save a game result to the database. Returns the result ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO game_results 
                (llm1_name, llm2_name, llm1_winnings, llm2_winnings, 
                 hands_played, session_date, llm1_config, llm2_config,
                 llm1_fallbacks, llm2_fallbacks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.llm1_name, result.llm2_name,
                result.llm1_winnings, result.llm2_winnings,
                result.hands_played, result.session_date,
                result.llm1_config, result.llm2_config,
                result.llm1_fallbacks, result.llm2_fallbacks
            ))
            return cursor.lastrowid
    
    def save_hand_log(self, hand_log: HandLog) -> int:
        """Save a hand log to the database. Returns the hand log ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO hand_logs 
                (session_id, hand_number, llm1_name, llm2_name, 
                 llm1_hole_cards, llm2_hole_cards, community_cards, actions,
                 pot_size, winner, llm1_winnings, llm2_winnings, hand_date,
                 showdown, hand_strength_llm1, hand_strength_llm2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hand_log.session_id, hand_log.hand_number,
                hand_log.llm1_name, hand_log.llm2_name,
                hand_log.llm1_hole_cards, hand_log.llm2_hole_cards,
                hand_log.community_cards, hand_log.actions,
                hand_log.pot_size, hand_log.winner,
                hand_log.llm1_winnings, hand_log.llm2_winnings,
                hand_log.hand_date, hand_log.showdown,
                hand_log.hand_strength_llm1, hand_log.hand_strength_llm2
            ))
            return cursor.lastrowid
    
    def get_all_results(self) -> List[GameResult]:
        """Get all game results from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT llm1_name, llm2_name, llm1_winnings, llm2_winnings,
                       hands_played, session_date, llm1_config, llm2_config,
                       COALESCE(llm1_fallbacks, 0) as llm1_fallbacks,
                       COALESCE(llm2_fallbacks, 0) as llm2_fallbacks
                FROM game_results
                ORDER BY session_date DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append(GameResult(
                    llm1_name=row['llm1_name'],
                    llm2_name=row['llm2_name'],
                    llm1_winnings=row['llm1_winnings'],
                    llm2_winnings=row['llm2_winnings'],
                    hands_played=row['hands_played'],
                    session_date=row['session_date'],
                    llm1_config=row['llm1_config'],
                    llm2_config=row['llm2_config'],
                    llm1_fallbacks=row['llm1_fallbacks'],
                    llm2_fallbacks=row['llm2_fallbacks']
                ))
            
            return results
    
    def get_results_for_llm(self, llm_name: str) -> List[GameResult]:
        """Get all results where the specified LLM participated."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT llm1_name, llm2_name, llm1_winnings, llm2_winnings,
                       hands_played, session_date, llm1_config, llm2_config
                FROM game_results
                WHERE llm1_name = ? OR llm2_name = ?
                ORDER BY session_date DESC
            """, (llm_name, llm_name))
            
            results = []
            for row in cursor.fetchall():
                results.append(GameResult(
                    llm1_name=row['llm1_name'],
                    llm2_name=row['llm2_name'],
                    llm1_winnings=row['llm1_winnings'],
                    llm2_winnings=row['llm2_winnings'],
                    hands_played=row['hands_played'],
                    session_date=row['session_date'],
                    llm1_config=row['llm1_config'],
                    llm2_config=row['llm2_config']
                ))
            
            return results
    
    def get_head_to_head_results(self, llm1: str, llm2: str) -> List[GameResult]:
        """Get all head-to-head results between two LLMs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT llm1_name, llm2_name, llm1_winnings, llm2_winnings,
                       hands_played, session_date, llm1_config, llm2_config
                FROM game_results
                WHERE (llm1_name = ? AND llm2_name = ?) 
                   OR (llm1_name = ? AND llm2_name = ?)
                ORDER BY session_date DESC
            """, (llm1, llm2, llm2, llm1))
            
            results = []
            for row in cursor.fetchall():
                results.append(GameResult(
                    llm1_name=row['llm1_name'],
                    llm2_name=row['llm2_name'],
                    llm1_winnings=row['llm1_winnings'],
                    llm2_winnings=row['llm2_winnings'],
                    hands_played=row['hands_played'],
                    session_date=row['session_date'],
                    llm1_config=row['llm1_config'],
                    llm2_config=row['llm2_config']
                ))
            
            return results
    
    def register_llm_config(self, name: str, provider: str, model: str, 
                           temperature: float = 0.7, config_json: str = "{}"):
        """Register an LLM configuration."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO llm_configs 
                (name, provider, model, temperature, config_json)
                VALUES (?, ?, ?, ?, ?)
            """, (name, provider, model, temperature, config_json))
    
    def get_registered_llms(self) -> List[Dict]:
        """Get all registered LLM configurations."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT name, provider, model, temperature, config_json
                FROM llm_configs
                ORDER BY name
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_hand_logs(self, session_id: Optional[int] = None, limit: int = 100) -> List[HandLog]:
        """Get hand logs from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if session_id:
                cursor = conn.execute("""
                    SELECT * FROM hand_logs 
                    WHERE session_id = ?
                    ORDER BY hand_number ASC
                    LIMIT ?
                """, (session_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM hand_logs 
                    ORDER BY hand_date DESC, hand_number DESC
                    LIMIT ?
                """, (limit,))
            
            hand_logs = []
            for row in cursor.fetchall():
                hand_logs.append(HandLog(
                    session_id=row['session_id'],
                    hand_number=row['hand_number'],
                    llm1_name=row['llm1_name'],
                    llm2_name=row['llm2_name'],
                    llm1_hole_cards=row['llm1_hole_cards'],
                    llm2_hole_cards=row['llm2_hole_cards'],
                    community_cards=row['community_cards'],
                    actions=row['actions'],
                    pot_size=row['pot_size'],
                    winner=row['winner'],
                    llm1_winnings=row['llm1_winnings'],
                    llm2_winnings=row['llm2_winnings'],
                    hand_date=row['hand_date'],
                    showdown=bool(row['showdown']),
                    hand_strength_llm1=row['hand_strength_llm1'],
                    hand_strength_llm2=row['hand_strength_llm2']
                ))
            
            return hand_logs
    
    def get_hand_logs_for_llm(self, llm_name: str, limit: int = 50) -> List[HandLog]:
        """Get hand logs for a specific LLM."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM hand_logs 
                WHERE llm1_name = ? OR llm2_name = ?
                ORDER BY hand_date DESC
                LIMIT ?
            """, (llm_name, llm_name, limit))
            
            hand_logs = []
            for row in cursor.fetchall():
                hand_logs.append(HandLog(
                    session_id=row['session_id'],
                    hand_number=row['hand_number'],
                    llm1_name=row['llm1_name'],
                    llm2_name=row['llm2_name'],
                    llm1_hole_cards=row['llm1_hole_cards'],
                    llm2_hole_cards=row['llm2_hole_cards'],
                    community_cards=row['community_cards'],
                    actions=row['actions'],
                    pot_size=row['pot_size'],
                    winner=row['winner'],
                    llm1_winnings=row['llm1_winnings'],
                    llm2_winnings=row['llm2_winnings'],
                    hand_date=row['hand_date'],
                    showdown=bool(row['showdown']),
                    hand_strength_llm1=row['hand_strength_llm1'],
                    hand_strength_llm2=row['hand_strength_llm2']
                ))
            
            return hand_logs

    def clear_results(self, confirm: bool = False):
        """Clear all results (use with caution!)."""
        if not confirm:
            raise ValueError("Must set confirm=True to clear results")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM game_results")
            conn.execute("DELETE FROM hand_logs")
            print("All results and hand logs cleared from database.")
