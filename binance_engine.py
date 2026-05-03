import os
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class BinanceEngine:
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.testnet = testnet
        
        try:
            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
            logger.info(f"BinanceEngine initialized. Testnet: {self.testnet}")
        except Exception as e:
            logger.error(f"Failed to initialize Binance Client: {e}")
            self.client = None

    def get_price(self, symbol: str) -> float:
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0

    def get_balance(self, asset: str = "USDT") -> float:
        try:
            balance = self.client.get_asset_balance(asset=asset)
            if balance:
                return float(balance['free'])
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance for {asset}: {e}")
            return 0.0

    def place_market_order(self, symbol: str, side: str, quantity: float):
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side.upper(),
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            return order
        except BinanceAPIException as e:
            logger.error(f"Binance API Error placing market order: {e}")
            return None
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None
