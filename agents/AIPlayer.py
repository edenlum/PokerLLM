from .Player import Player
from pydantic import BaseModel, Field
from typing import Literal

try:
    from ai_client import AIClient
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AI_CLIENT_AVAILABLE = False
    AIClient = None
    

SYSTEM_PROMPT = """You are an expert Texas Hold'em poker player. Analyze the situation and make the optimal decision.

Guidelines:
- Consider hand strength, position, pot odds, and opponent behavior
- Only use actions from the legal actions list
- Think about expected value and risk management"""

class AIPlayerResponse(BaseModel):
    reasoning: str = Field(..., description="A brief strategic explanation")
    action: Literal["check", "call", "raise", "fold", "bet"] = Field(..., description="The action to take")
    amount: int = Field(0, description="The amount to bet or raise")

class AIPlayer(Player):
    """AI-powered poker player that uses language models to make decisions."""
    
    def __init__(self, name: str, stack: int, provider: str, model: str):
        """
        Initialize AI player.
        
        Args:
            name: Player name
            stack: Starting chip stack
            provider: AI provider to use ('openai', 'google', 'anthropic')
            model: Specific model to use (if None, uses provider default)
        """
        super().__init__(name, stack)
        self.provider = provider
        self.model = model
        self._last_reasoning = None  # Store reasoning for hand logger
        
        # Initialize AI client
        if not AI_CLIENT_AVAILABLE:
            print(f"Warning: AI client not available (missing dependencies)")
            self.ai_client = None
        else:
            try:
                self.ai_client = AIClient(provider=provider, model=model, log_file=f"logs/{name}.log")
            except Exception as e:
                print(f"Warning: Failed to initialize AI client: {e}")
                raise e
                
    def get_raw_action(self, game_history: str, legal_actions: list[str], amount_to_call: int, error_message: str = "") -> tuple[str, int]:
        """
        Get AI player's raw action. Returns (action, amount) tuple.
        Validation is handled by the parent class.
            
        Args:
            game_history: Game history so far
            legal_actions: List of valid actions
            amount_to_call: Amount needed to call
            error_message: Error message from previous attempt (if any)
            
        Returns:
            tuple: (action, amount) - raw response that may need validation
        """
        if not self.ai_client:
            raise ValueError(f"🤖 {self.name}: No AI client available")

        # Create enhanced prompt
        prompt = self._create_ai_prompt(game_history, legal_actions, amount_to_call, error_message)
        
        try:
            # Get AI response
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            ai_response = self.ai_client.get_completion(
                messages=messages,
                response_format=AIPlayerResponse
            )
            
            # Parse AI response into raw action and amount
            action, amount, reasoning = self._parse_ai_response(ai_response)
            
            print(f"🤖 {self.name}: Attempting {action}" + (f" {amount}" if amount > 0 else ""))
            if reasoning:
                print(f"   Reasoning: {reasoning}")
            
            return action, amount
            
        except Exception as e:
            raise ValueError(f"🤖 {self.name}: AI error: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI poker decisions."""
        return SYSTEM_PROMPT
    
    def _create_ai_prompt(self, game_history: str, legal_actions: list, amount_to_call: int, error_message: str = "") -> str:
        """Create prompt for AI decision."""
        prompt_parts = [game_history]
        
        if error_message:
            prompt_parts.extend([
                "",
                f"ERROR: Your last action was invalid: {error_message}",
                "Please choose a valid action this time.",
            ])
        
        prompt_parts.append("\nRespond in the specified format.")
        return "\n".join(prompt_parts)
    
    def _parse_ai_response(self, response: AIPlayerResponse) -> tuple[str, int, str]:
        """Parse AI response into action, amount, and reasoning."""
        # Store reasoning for hand logger to access
        self._last_reasoning = response.reasoning
        return response.action, response.amount, response.reasoning