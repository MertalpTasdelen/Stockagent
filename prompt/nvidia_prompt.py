"""
NVIDIA-specific simplified prompts
Tek hisse analizi icin basitlestirilmis prompt'lar
"""

from procoder.prompt import *

NVIDIA_BACKGROUND = NamedBlock(
    name="Background",
    content="""
You are a professional stock analyst specializing in NVIDIA (NVDA) stock.
Your task is to analyze current market conditions and make a trading decision: BUY, SELL, or HOLD.
    """
)

NVIDIA_ANALYSIS_PROMPT = NamedBlock(
    name="Analysis",
    content="""
Current Status:
- Date: Day {date}
- Current NVIDIA Price: ${stock_price} per share
- Your Holdings: {stock_amount} shares
- Available Cash: ${cash}
- Character: {character}

Recent Market Data:
- Recent deals: {stock_deals}

Task:
Based on the current price, your holdings, and market conditions, decide whether to:
1. BUY more NVIDIA shares (if you believe price will increase)
2. SELL some/all NVIDIA shares (if you believe price will decrease)
3. HOLD (no action, wait for better opportunity)

Return your decision in JSON format:
- To BUY: {{"action_type": "buy", "stock": "A", "amount": 100, "price": {stock_price}}}
- To SELL: {{"action_type": "sell", "stock": "A", "amount": 50, "price": {stock_price}}}
- To HOLD: {{"action_type": "no"}}

Important: 
- "stock" must always be "A" (representing NVIDIA)
- "amount" is number of shares (must be positive integer)
- "price" should be current market price ${stock_price}
- You cannot buy more than cash allows: max {max_buy} shares
- You cannot sell more than you own: max {stock_amount} shares
    """
)

NVIDIA_RETRY_PROMPT = NamedBlock(
    name="Retry",
    content="""
Your previous response had formatting issues: {fail_response}

Please provide a valid JSON response:
- To BUY: {{"action_type": "buy", "stock": "A", "amount": 100, "price": {stock_price}}}
- To SELL: {{"action_type": "sell", "stock": "A", "amount": 50, "price": {stock_price}}}
- To HOLD: {{"action_type": "no"}}
    """
)
