# LLM Poker Benchmark

A simple benchmark system for evaluating Large Language Models (LLMs) in heads-up poker games.

## Overview

This benchmark runs heads-up cash games between different LLMs and tracks their performance. Each LLM starts with 100 big blinds (10,000 chips with 50/100 blinds) and plays until a maximum number of hands or until one player busts.

## Quick Start

### 1. Register LLMs for Testing

```bash
# Register OpenAI GPT-4
python benchmark/cli.py register "gpt-4-turbo" openai gpt-4-turbo --temperature 0.7

# Register Google Gemini
python benchmark/cli.py register "gemini-pro" google gemini-pro --temperature 0.8

# Register Claude (if available)
python benchmark/cli.py register "claude-3" anthropic claude-3-sonnet-20240229 --temperature 0.7
```

### 2. List Registered LLMs

```bash
python benchmark/cli.py list-llms
```

### 3. Run Individual Session

```bash
# Run 1000 hands between two LLMs
python benchmark/cli.py run-session "gpt-4-turbo" "gemini-pro" --hands 1000
```

### 4. Run Full Tournament

```bash
# Run round-robin tournament (all pairs)
python benchmark/cli.py run-tournament --hands 1000
```

### 5. View Results

```bash
# Show leaderboard
python benchmark/cli.py leaderboard

# Show detailed results
python benchmark/cli.py results --limit 5

# Show results for specific LLM
python benchmark/cli.py results --llm "gpt-4-turbo"
```

## How It Works

### Game Format
- **Heads-up cash games** (2 players)
- **Starting stack:** 10,000 chips (100 big blinds)
- **Blinds:** 50/100 (small/big blind)
- **Session length:** Up to 1000 hands or until one player busts

### Scoring System
- **Primary metric:** Average chips won per hand across all opponents
- **Formula:** `(Final Stack - Starting Stack) / Hands Played`
- **Leaderboard:** Ranked by average winnings per hand

### Database Schema
Results are stored in SQLite database with:
- Game results (winnings, hands played, date)
- LLM configurations (provider, model, temperature)
- Session metadata

## Example Output

```
🏆 LLM Poker Leaderboard
======================================================================
Rank LLM Name             Avg/Hand     Total Hands  Sessions  
----------------------------------------------------------------------
1    gpt-4-turbo         +12.45       2000         2         
2    claude-3            +8.32        2000         2         
3    gemini-pro          -10.38       2000         2         
======================================================================
Note: Avg/Hand = Average chips won per hand across all opponents
```

## API Keys Setup

Set environment variables for the LLMs you want to test:

```bash
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"  
export ANTHROPIC_API_KEY="your-anthropic-key"
```

Or pass them directly when registering:

```bash
python benchmark/cli.py register "gpt-4" openai gpt-4-turbo --api-key "your-key"
```

## Adding New LLMs

To add a new LLM to an existing benchmark:

1. Register the new LLM
2. Run tournament again (only new pairings will be played)
3. View updated leaderboard

The system automatically handles incremental updates.

## Files Structure

```
benchmark/
├── __init__.py          # Package initialization
├── database.py          # Database operations and schema
├── runner.py           # Core benchmark logic
├── cli.py              # Command-line interface
├── README.md           # This file
└── results.db          # SQLite database (created automatically)
```

## Technical Details

### Performance Considerations
- Each session can take 10-30 minutes depending on LLM response times
- Full tournament with N LLMs requires N*(N-1)/2 sessions
- Results are saved incrementally (safe to interrupt and resume)

### Error Handling
- Failed API calls fall back to simple actions
- Sessions continue even if individual hands fail
- All errors are logged with context

### Extensibility
- Easy to add new providers in `ai_client.py`
- Database schema supports additional metadata
- CLI can be extended with new commands

## Limitations

- Currently only supports heads-up games
- No side pot handling for complex all-in scenarios
- Simple scoring system (doesn't account for opponent strength)
- No statistical significance testing yet

## Future Enhancements

- Multi-way games (6-max tables)
- ELO rating system
- Statistical significance testing
- Tournament format benchmarks
- Real-time progress tracking
- Web interface for results
