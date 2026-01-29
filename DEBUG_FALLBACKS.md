# 🔍 Debugging High Fallback Rates in LLM Poker

## Overview
High fallback rates indicate that LLMs are failing to generate valid poker actions. This guide helps you identify and fix common issues.

## 🚀 Quick Debugging

### 1. Use the Debug Command
```bash
# Debug a specific LLM
python3 benchmark/cli.py debug-llm claude-sonnet-4.5 --hands 5 --verbose

# Quick test without verbose output
python3 benchmark/cli.py debug-llm gpt-4o-mini --hands 3
```

### 2. Check Current Fallback Rates
```bash
# View leaderboard with fallback percentages
python3 benchmark/cli.py leaderboard
```

## 🔍 Common Issues & Solutions

### Issue 1: Missing Dependencies
**Symptoms**: `No AI client available` errors
**Solution**: Install required packages
```bash
pip install openai python-dotenv
```

### Issue 2: Missing API Keys
**Symptoms**: Authentication errors, API failures
**Solution**: Set up environment variables
```bash
export OPENROUTER_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
```

### Issue 3: Invalid Action Format
**Symptoms**: `Invalid action 'X'. Legal actions: [...]`
**Root Cause**: LLM not following expected response format
**Solutions**:
- Check if LLM supports structured output (Pydantic models)
- Adjust temperature (lower = more consistent)
- Improve prompt engineering

### Issue 4: Invalid Bet Amounts
**Symptoms**: 
- `Amount must be positive for bet/raise`
- `Raise amount (X) must be greater than amount to call (Y)`
- `Cannot bet to X - need Y chips but only have Z`

**Solutions**:
- Check if LLM understands poker betting rules
- Verify stack sizes are being communicated correctly
- Consider adding examples to prompts

### Issue 5: Wrong Action Types
**Symptoms**: 
- `Cannot bet when there's already a bet to call. Use 'raise' instead`
- `Action 'call' should not have an amount`

**Solutions**:
- Improve prompt clarity about bet vs raise
- Add examples of correct action formats
- Check if LLM understands poker terminology

## 📊 Analyzing Patterns

### View Detailed Error Patterns
The debug command shows:
- **Total fallback rate**: Overall percentage of failed actions
- **Common errors**: Most frequent validation failures
- **Action patterns**: Which actions the LLM attempts most often
- **Validation attempts**: How many tries before giving up

### Example Debug Output Analysis
```
🚨 Most Common Errors:
   8x: Raise amount (50) must be greater than amount to call (100)
   5x: Invalid action 'bet'. Legal actions: ['fold', 'call', 'raise']
   3x: Cannot bet to 150 - need 150 chips but only have 100
```

**Interpretation**:
- LLM doesn't understand raise sizing (8 failures)
- LLM confuses bet vs raise (5 failures)  
- LLM doesn't track stack sizes properly (3 failures)

## 🛠️ Fixing Specific LLMs

### High Fallback Rate (>50%)
1. **Check API connectivity** first
2. **Verify response format** - ensure LLM supports structured output
3. **Lower temperature** (0.3-0.5) for more consistent responses
4. **Simplify prompts** - remove complex instructions

### Medium Fallback Rate (10-50%)
1. **Improve prompt engineering**
2. **Add more examples** of correct actions
3. **Check specific error patterns** with debug command
4. **Adjust validation rules** if too strict

### Low Fallback Rate (<10%)
1. **Monitor for edge cases**
2. **Check performance under different scenarios**
3. **Consider this acceptable** for production use

## 🎯 Best Practices

### 1. Prompt Engineering
```python
# Good: Clear, specific instructions
"Choose one action: fold, call, or raise. 
For raise, specify total amount (not additional).
Example: raise 200 (to raise to 200 total)"

# Bad: Vague instructions
"Make a poker decision"
```

### 2. Temperature Settings
- **0.1-0.3**: Very consistent, may be too rigid
- **0.5-0.7**: Good balance (recommended)
- **0.8-1.0**: More creative, higher fallback risk

### 3. Model Selection
- **Larger models**: Generally better at following instructions
- **Chat-optimized models**: Better for interactive tasks
- **Code models**: May be better at structured output

### 4. Validation Tuning
Consider if validation rules are too strict:
```python
# Maybe too strict?
if action == 'raise' and amount <= amount_to_call:
    return f"Raise amount ({amount}) must be greater than amount to call ({amount_to_call})"

# More lenient alternative?
if action == 'raise' and amount < amount_to_call + min_raise:
    return f"Minimum raise is {amount_to_call + min_raise}"
```

## 📈 Monitoring & Improvement

### Regular Health Checks
```bash
# Weekly fallback rate check
python3 benchmark/cli.py leaderboard | grep "Fallback%"

# Debug problematic LLMs
python3 benchmark/cli.py debug-llm <high-fallback-llm> --hands 10
```

### Performance Tracking
- **Target**: <10% fallback rate for production LLMs
- **Acceptable**: 10-20% for experimental models
- **Problematic**: >20% needs investigation

### Continuous Improvement
1. **Log all validation failures** for analysis
2. **A/B test prompt changes** 
3. **Monitor after model updates**
4. **Share findings** with LLM providers

## 🔧 Advanced Debugging

### Custom Validation Rules
You can modify validation in `agents/Player.py`:
```python
def validate_action(self, action: str, amount: int, legal_actions: list, amount_to_call: int) -> str:
    # Add custom validation logic here
    # Return empty string if valid, error message if invalid
```

### Logging Integration
Add to your debugging workflow:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed AI client interactions
```

### Database Analysis
Query the database directly for patterns:
```sql
SELECT llm1_name, AVG(llm1_fallbacks * 100.0 / hands_played) as fallback_rate
FROM game_results 
GROUP BY llm1_name 
ORDER BY fallback_rate DESC;
```

## 📞 Getting Help

1. **Check this guide** for common issues
2. **Use debug command** for specific LLM analysis
3. **Review validation logs** for patterns
4. **Test with different temperatures/prompts**
5. **Consider model limitations** - some LLMs may not be suitable for structured poker decisions

---

*This debugging system helps maintain high-quality LLM poker performance by identifying and fixing validation issues quickly.*

