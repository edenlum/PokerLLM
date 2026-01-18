#!/usr/bin/env python3
"""
Site generator for the LLM Poker Benchmark GitHub Pages site.
Reads data from the benchmark database and generates static JSON data files.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Add parent directory to path to import benchmark modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.database import BenchmarkDatabase
from benchmark.runner import BenchmarkRunner


class SiteGenerator:
    """Generates static site data from benchmark database."""
    
    def __init__(self, db_path: str = "benchmark/results.db", output_dir: str = "docs"):
        """
        Initialize the site generator.
        
        Args:
            db_path: Path to the benchmark database
            output_dir: Directory to output the generated site files
        """
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.db = BenchmarkDatabase(db_path)
        self.runner = BenchmarkRunner(db_path)
    
    def generate_site(self):
        """Generate the complete static site."""
        print("🚀 Generating LLM Poker Benchmark site...")
        
        try:
            # Generate data files
            self.generate_data_js()
            
            print("✅ Site generation completed successfully!")
            print(f"📁 Output directory: {self.output_dir.absolute()}")
            print(f"🌐 Open {self.output_dir}/index.html in a browser to view the site")
            
        except Exception as e:
            print(f"❌ Site generation failed: {e}")
            raise
    
    def generate_data_js(self):
        """Generate the data.js file with all benchmark data."""
        print("📊 Generating benchmark data...")
        
        # Collect all data
        data = {
            "lastUpdated": datetime.now().isoformat(),
            "leaderboard": self.get_leaderboard_data(),
            "pairwiseResults": self.get_pairwise_data(),
            "recentMatches": self.get_recent_matches_data(),
            "handLogs": self.get_hand_logs_data(),
            "stats": self.get_stats_data()
        }
        
        # Generate JavaScript file
        js_content = self.generate_js_content(data)
        
        # Write to file
        output_file = self.output_dir / "assets" / "js" / "data.js"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        print(f"✅ Generated {output_file}")
        print(f"   - {len(data['leaderboard'])} LLMs in leaderboard")
        print(f"   - {len(data['recentMatches'])} recent matches")
        print(f"   - {len(data['handLogs'])} hand logs")
        print(f"   - {data['stats']['totalSessions']} total sessions")
    
    def get_leaderboard_data(self) -> List[Dict[str, Any]]:
        """Get leaderboard data."""
        leaderboard = self.runner.get_leaderboard()
        
        # Get registered LLMs to map names to provider/model
        registered_llms = {llm['name']: llm for llm in self.db.get_registered_llms()}
        
        result = []
        for rank, (llm_name, avg_per_hand, total_hands, sessions, fallback_rate) in enumerate(leaderboard, 1):
            # Calculate win rate from pairwise results
            win_rate = self.calculate_win_rate(llm_name)
            
            # Get provider and model from registered LLMs
            llm_info = registered_llms.get(llm_name, {})
            
            result.append({
                "rank": rank,
                "name": llm_name,
                "provider": llm_info.get('provider', ''),
                "model": llm_info.get('model', ''),
                "avgPerHand": round(avg_per_hand, 2),
                "totalHands": total_hands,
                "sessions": sessions,
                "fallbackRate": round(fallback_rate, 1),
                "winRate": round(win_rate, 1)
            })
        
        return result
    
    def get_pairwise_data(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get pairwise matchup data."""
        all_results = self.db.get_all_results()
        
        # Group results by LLM pairs
        pairwise = {}
        
        for result in all_results:
            llm1, llm2 = result.llm1_name, result.llm2_name
            
            # Initialize nested dictionaries
            if llm1 not in pairwise:
                pairwise[llm1] = {}
            if llm2 not in pairwise:
                pairwise[llm2] = {}
            
            # Add result for llm1 vs llm2
            if llm2 not in pairwise[llm1]:
                pairwise[llm1][llm2] = {
                    "avgWinnings": 0,
                    "winRate": 0,
                    "sessions": 0,
                    "totalHands": 0,
                    "fallbacks": 0,
                    "totalWinnings": 0,
                    "wins": 0
                }
            
            # Add result for llm2 vs llm1
            if llm1 not in pairwise[llm2]:
                pairwise[llm2][llm1] = {
                    "avgWinnings": 0,
                    "winRate": 0,
                    "sessions": 0,
                    "totalHands": 0,
                    "fallbacks": 0,
                    "totalWinnings": 0,
                    "wins": 0
                }
            
            # Update llm1's stats vs llm2
            pairwise[llm1][llm2]["sessions"] += 1
            pairwise[llm1][llm2]["totalHands"] += result.hands_played
            pairwise[llm1][llm2]["totalWinnings"] += result.llm1_winnings
            pairwise[llm1][llm2]["fallbacks"] += getattr(result, 'llm1_fallbacks', 0)
            if result.llm1_winnings > 0:
                pairwise[llm1][llm2]["wins"] += 1
            
            # Update llm2's stats vs llm1
            pairwise[llm2][llm1]["sessions"] += 1
            pairwise[llm2][llm1]["totalHands"] += result.hands_played
            pairwise[llm2][llm1]["totalWinnings"] += result.llm2_winnings
            pairwise[llm2][llm1]["fallbacks"] += getattr(result, 'llm2_fallbacks', 0)
            if result.llm2_winnings > 0:
                pairwise[llm2][llm1]["wins"] += 1
        
        # Calculate final averages
        for llm1 in pairwise:
            for llm2 in pairwise[llm1]:
                data = pairwise[llm1][llm2]
                if data["totalHands"] > 0:
                    data["avgWinnings"] = round(data["totalWinnings"] / data["totalHands"], 2)
                if data["sessions"] > 0:
                    data["winRate"] = round((data["wins"] / data["sessions"]) * 100, 1)
                
                # Remove temporary fields
                del data["totalWinnings"]
                del data["wins"]
        
        return pairwise
    
    def get_recent_matches_data(self) -> List[Dict[str, Any]]:
        """Get recent matches data."""
        all_results = self.db.get_all_results()
        
        # Sort by date (most recent first)
        sorted_results = sorted(all_results, key=lambda x: x.session_date, reverse=True)
        
        recent_matches = []
        for result in sorted_results[:10]:  # Last 10 matches
            recent_matches.append({
                "date": result.session_date,
                "llm1": result.llm1_name,
                "llm2": result.llm2_name,
                "llm1Winnings": round(result.llm1_winnings, 1),
                "llm2Winnings": round(result.llm2_winnings, 1),
                "handsPlayed": result.hands_played,
                "llm1Fallbacks": getattr(result, 'llm1_fallbacks', 0),
                "llm2Fallbacks": getattr(result, 'llm2_fallbacks', 0)
            })
        
        return recent_matches
    
    def get_hand_logs_data(self) -> List[Dict[str, Any]]:
        """Get hand logs data for the website."""
        hand_logs = self.db.get_hand_logs(limit=500)  # Get recent 500 hands
        
        result = []
        for hand_log in hand_logs:
            result.append({
                "session_id": hand_log.session_id,
                "hand_number": hand_log.hand_number,
                "llm1_name": hand_log.llm1_name,
                "llm2_name": hand_log.llm2_name,
                "llm1_hole_cards": hand_log.llm1_hole_cards,
                "llm2_hole_cards": hand_log.llm2_hole_cards,
                "community_cards": hand_log.community_cards,
                "actions": hand_log.actions,
                "pot_size": hand_log.pot_size,
                "winner": hand_log.winner,
                "llm1_winnings": round(hand_log.llm1_winnings, 2),
                "llm2_winnings": round(hand_log.llm2_winnings, 2),
                "hand_date": hand_log.hand_date,
                "showdown": hand_log.showdown,
                "hand_strength_llm1": hand_log.hand_strength_llm1,
                "hand_strength_llm2": hand_log.hand_strength_llm2
            })
        
        return result
    
    def get_stats_data(self) -> Dict[str, int]:
        """Get overall statistics."""
        all_results = self.db.get_all_results()
        llms = self.db.get_registered_llms()
        
        total_hands = sum(result.hands_played for result in all_results)
        
        return {
            "totalLLMs": len(llms),
            "totalSessions": len(all_results),
            "totalHands": total_hands
        }
    
    def calculate_win_rate(self, llm_name: str) -> float:
        """Calculate win rate for an LLM across all opponents."""
        all_results = self.db.get_all_results()
        
        wins = 0
        total_sessions = 0
        
        for result in all_results:
            if result.llm1_name == llm_name:
                total_sessions += 1
                if result.llm1_winnings > 0:
                    wins += 1
            elif result.llm2_name == llm_name:
                total_sessions += 1
                if result.llm2_winnings > 0:
                    wins += 1
        
        return (wins / total_sessions * 100) if total_sessions > 0 else 0
    
    def generate_js_content(self, data: Dict[str, Any]) -> str:
        """Generate JavaScript content for data.js file."""
        
        js_template = '''// This file is auto-generated by benchmark/site_generator.py
// Last updated: {timestamp}

window.benchmarkData = {data_json};

// Helper functions for data access
window.getBenchmarkStats = function() {{
    return window.benchmarkData.stats;
}};

window.getLeaderboard = function() {{
    return window.benchmarkData.leaderboard;
}};

window.getPairwiseResults = function() {{
    return window.benchmarkData.pairwiseResults;
}};

window.getRecentMatches = function() {{
    return window.benchmarkData.recentMatches;
}};

window.formatDate = function(dateString) {{
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}});
}};

window.formatNumber = function(num, decimals = 2) {{
    if (num > 0) {{
        return '+' + num.toFixed(decimals);
    }}
    return num.toFixed(decimals);
}};

window.getFallbackClass = function(rate) {{
    if (rate < 1) return 'fallback-low';
    if (rate < 5) return 'fallback-medium';
    return 'fallback-high';
}};

window.getPerformanceClass = function(value) {{
    if (value > 0) return 'positive';
    if (value < 0) return 'negative';
    return 'neutral';
}};'''
        
        return js_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            data_json=json.dumps(data, indent=2)
        )


def main():
    """Main entry point for the site generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate LLM Poker Benchmark GitHub Pages site')
    parser.add_argument('--db', default='benchmark/results.db', help='Path to benchmark database')
    parser.add_argument('--output', default='docs', help='Output directory for generated site')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"❌ Database not found: {args.db}")
        print("Run some benchmark sessions first to generate data.")
        sys.exit(1)
    
    # Generate site
    generator = SiteGenerator(args.db, args.output)
    generator.generate_site()


if __name__ == '__main__':
    main()
