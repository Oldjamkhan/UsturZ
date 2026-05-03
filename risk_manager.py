import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_risk_per_trade_pct: float = 1.0, max_open_positions: int = 3, max_daily_drawdown_pct: float = 5.0):
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_open_positions = max_open_positions
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.current_open_positions = 0
        self.consecutive_losses = 0
        self.daily_drawdown_pct = 0.0

    def can_open_trade(self) -> bool:
        if self.consecutive_losses >= 3:
            logger.warning("Kill switch activated: 3 consecutive losses.")
            return False
        
        if self.current_open_positions >= self.max_open_positions:
            logger.warning(f"Max open positions reached ({self.max_open_positions}).")
            return False
            
        if self.daily_drawdown_pct >= self.max_daily_drawdown_pct:
            logger.warning(f"Daily drawdown limit reached ({self.max_daily_drawdown_pct}%).")
            return False
            
        return True

    def calculate_position_size(self, account_balance: float, entry_price: float, stop_loss: float) -> float:
        if not self.can_open_trade():
            return 0.0
            
        risk_amount = account_balance * (self.max_risk_per_trade_pct / 100.0)
        stop_loss_pct = abs(entry_price - stop_loss) / entry_price
        
        if stop_loss_pct == 0:
            return 0.0
            
        # size = Risk Amount / (Entry Price * Stop Loss %)
        position_size = risk_amount / (entry_price * stop_loss_pct)
        return position_size

    def record_trade_result(self, pnl: float):
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
