# 🎮 Play Against AI - Web Implementation Plan

## Overview
Add an interactive web-based poker game where users can play heads-up poker against LLMs directly in the browser. This would be a great addition to the existing benchmark site, allowing users to experience the AI opponents firsthand.

## 🏗️ Architecture Options

### Option 1: Client-Server with Backend API ⭐ (Recommended)
- **Frontend**: Interactive poker UI in JavaScript
- **Backend**: Flask/FastAPI server running existing poker engine
- **LLM Integration**: Server makes API calls to LLM providers
- **Real-time**: WebSockets for live game updates
- **Pros**: Secure API key handling, reuses existing code, real-time updates
- **Cons**: Requires server hosting, more complex deployment

### Option 2: Serverless Functions
- **Frontend**: Static site (extends current GitHub Pages)
- **Backend**: Vercel/Netlify functions for game logic
- **State**: Store game state in browser localStorage or simple DB
- **LLM Calls**: Functions make API calls to providers
- **Pros**: Easier deployment, scales automatically
- **Cons**: Cold starts, state management complexity

### Option 3: Hybrid Approach
- **Current Site**: Keep static leaderboard/results
- **New Section**: Interactive poker game with backend
- **Integration**: Games can optionally contribute to benchmark data
- **Pros**: Best of both worlds
- **Cons**: More complex architecture

## 🎯 Key Components Needed

### Frontend (JavaScript)
```javascript
// Interactive poker table components:
- Card animations and dealing
- Action buttons (fold, call, raise)
- Chip betting interface with slider/input
- Real-time game state updates
- Chat/reasoning display from AI
- Hand history viewer
- Statistics dashboard
```

### Backend API Endpoints
```python
POST /api/game/start     # Start new game vs selected LLM
POST /api/game/action    # Submit player action (fold/call/raise)
GET  /api/game/state     # Get current game state
POST /api/game/reset     # Reset/start new hand
GET  /api/llms          # Get available LLM opponents
GET  /api/game/history  # Get hand history
```

### Game State Management
- Session handling for multiple concurrent games
- Game history and hand logging (reuse existing HandLogger)
- Integration with existing benchmark database
- Player statistics tracking

## 🔐 Security & API Keys

### Challenge
LLM API calls need credentials but can't be exposed to frontend.

### Solutions
1. **Server-side calls**: Keep API keys on backend (most secure) ⭐
2. **Rate limiting**: Prevent abuse of free games (e.g., 10 games/day per IP)
3. **Optional registration**: For tracking personal stats and leaderboards
4. **Environment variables**: Store API keys securely on server

## 🚀 Implementation Phases

### Phase 1: Basic Web Game (MVP)
- [ ] Simple heads-up poker UI
- [ ] Flask backend with game API
- [ ] Human vs one selected LLM (e.g., GPT-4)
- [ ] Basic game state management
- [ ] Reuse existing Game, Player, AIPlayer classes

### Phase 2: Enhanced Features
- [ ] Multiple LLM opponents to choose from
- [ ] Game history and personal statistics
- [ ] Integration with benchmark database
- [ ] Improved UI with animations
- [ ] AI reasoning display

### Phase 3: Advanced Features
- [ ] Real-time multiplayer (human vs human vs LLM)
- [ ] Tournament modes
- [ ] Advanced analytics and hand review
- [ ] Leaderboards for human players
- [ ] Mobile-responsive design

## 💡 Technical Implementation Details

### Reuse Existing Code
- ✅ `Game` class: Core poker logic
- ✅ `Player`, `AIPlayer` classes: Player management
- ✅ `HandLogger`: Capture web games for analysis
- ✅ `BenchmarkDatabase`: Store web game results
- ✅ LLM configurations from benchmark system

### New Components Needed
- `WebHumanPlayer`: Gets actions from HTTP requests instead of input()
- `GameSession`: Manage web game state and sessions
- WebSocket handler for real-time updates (optional)
- Web UI components for poker table

### Example WebHumanPlayer
```python
class WebHumanPlayer(Player):
    def __init__(self, name, stack, session_id):
        super().__init__(name, stack)
        self.session_id = session_id
        self.pending_action = None
    
    def get_raw_action(self, game_history, legal_actions, amount_to_call, error_message=""):
        # Store game state and wait for web action
        # This would be handled by the web API
        return self.pending_action
```

## 🎨 User Experience Mockup

```
┌─────────────────────────────────────────────────────┐
│  🃏 Poker vs AI - Choose Your Opponent              │
├─────────────────────────────────────────────────────┤
│  [GPT-4 Turbo] [Claude 3.5] [Gemini Pro] [More...] │
│                                                     │
│         🂡 🂱         POT: $150                     │
│      AI Opponent                                    │
│       Stack: $850                                   │
│                                                     │
│    🃏 🃏 🃏 🃏 🃏                                   │
│       Community Cards                               │
│                                                     │
│         YOU                                         │
│       Stack: $850                                   │
│         🂠 🂠                                       │
│                                                     │
│  [Fold] [Call $50] [Raise] [___] [All-in]         │
│                                                     │
│  💭 AI Reasoning: "I have top pair with a good     │
│     kicker. The pot odds are favorable, so I'm     │
│     betting for value and protection."              │
│                                                     │
│  📊 Session Stats: Hands: 15 | Won: 8 | BB/100: +5 │
└─────────────────────────────────────────────────────┘
```

## 🤔 Questions & Decisions Needed

### 1. Deployment Preference
- **Flask/FastAPI + traditional hosting** (Heroku, DigitalOcean, AWS)
- **Serverless functions** (Vercel, Netlify)
- **Docker container** (easier deployment)

### 2. API Keys & Costs
- Are you willing to provide API keys for public web version?
- Should there be usage limits to control costs?
- Consider offering "demo mode" with limited free games?

### 3. Database Integration
- Should web games contribute to benchmark database?
- Track human player statistics separately?
- Anonymous vs registered users?

### 4. Feature Scope for MVP
- Start with basic 1v1 poker?
- Include multiple LLM opponents from day 1?
- Add tournament features later?

### 5. Hosting & Domain
- Host on same domain as current GitHub Pages site?
- Separate subdomain (e.g., play.poker-benchmark.com)?
- Use existing poker repository or create new one?

## 📋 Next Steps

1. **Decide on architecture** (recommend Option 1: Flask backend)
2. **Set up development environment** with Flask + existing poker code
3. **Create basic API endpoints** for game management
4. **Build minimal poker UI** with HTML/CSS/JavaScript
5. **Test with one LLM opponent** (GPT-4 or Claude)
6. **Deploy MVP** and gather feedback
7. **Iterate and add features** based on usage

## 🔗 Related Files
- `benchmark/database.py` - Database schema and operations
- `benchmark/runner.py` - Game session management
- `agents/AIPlayer.py` - LLM integration
- `simulator/Game.py` - Core poker logic
- `benchmark/hand_logger.py` - Hand logging for analysis

---

*This document will be updated as we make progress on the implementation.*
