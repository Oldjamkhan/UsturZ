import schedule
import time
import asyncio
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DailyReporter:
    def __init__(self, ai_engine, bot, owner_id):
        self.ai = ai_engine
        self.bot = bot
        self.owner_id = owner_id
        
        # Schedule the reports
        schedule.every().day.at("09:00").do(self.generate_and_send_report, report_type="ERTALABKI")
        schedule.every().day.at("20:00").do(self.generate_and_send_report, report_type="KECHKI")
        
        logger.info("DailyReporter initialized. Scheduled for 09:00 and 20:00.")

    def generate_and_send_report(self, report_type="ERTALABKI"):
        # We need to run the async send_message in the event loop
        asyncio.create_task(self._async_send(report_type))

    async def _async_send(self, report_type):
        logger.info(f"Generating {report_type} report...")
        
        # Get data from Binance
        btc_price = self.ai.binance.get_price("BTCUSDT")
        usdt_bal = self.ai.binance.get_balance("USDT")
        
        # Prepare text for AI to synthesize
        raw_data = f"""
        Type: {report_type} REPORT
        Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        BTC Price: {btc_price}
        USDT Balance: {usdt_bal}
        Open Positions: {self.ai.risk.current_open_positions}
        Daily Drawdown: {self.ai.risk.daily_drawdown_pct}%
        """
        
        # Ask AI to generate a beautiful report
        prompt = f"Sen hozir moliyaviy analitiksan. Mana bu ma'lumotlarga asoslanib, Jamshidbek uchun qisqa, aniq va professional Telegram hisobotini yozib ber (O'zbek tilida). Emojilardan o'rinli foydalan:\n{raw_data}"
        
        try:
            model = self.ai.chat_sessions[f"{self.owner_id}_owner"]
            response = model.send_message(prompt)
            report_text = response.text
            
            await self.bot.send_message(chat_id=self.owner_id, text=report_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            await self.bot.send_message(chat_id=self.owner_id, text=f"⚠️ {report_type} hisobotini yaratishda xatolik yuz berdi: {e}")

    def run_scheduler_loop(self):
        """This should be run in a separate background thread"""
        while True:
            schedule.run_pending()
            time.sleep(60) # Check every minute
