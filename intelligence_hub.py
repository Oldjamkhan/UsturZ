import logging
import asyncio
from perplexity_news import PerplexityNews
from telegram_intelligence import TelegramIntelligence

logger = logging.getLogger(__name__)

class IntelligenceHub:
    def __init__(self, ai_engine):
        self.ai = ai_engine
        self.perplexity = PerplexityNews()
        self.telegram = TelegramIntelligence()
        
        # Add channels to monitor
        self.target_channels = ["@whale_alert", "@CryptoBanterGroup"] 
        
        logger.info("IntelligenceHub initialized.")

    async def get_daily_synthesis(self):
        logger.info("Gathering daily intelligence...")
        
        # 1. Get Market News
        news = self.perplexity.get_market_news()
        
        # 2. Get Telegram Signals
        # Ensure client is started
        if self.telegram.client:
            await self.telegram.start()
            tg_signals = await self.telegram.monitor_channels(self.target_channels)
        else:
            tg_signals = "Telegram API ishga tushirilmagan."
            
        # 3. Combine and Synthesize via Gemini
        prompt = f"""
        Sen moliyaviy intelligence tizimisan. Quyidagi ma'lumotlarni tahlil qilib, 
        Jamshidbek uchun trading signallari va bozorning umumiy xulosasini yoz.
        
        [PERPLEXITY YANGILIKLARI]:
        {news}
        
        [TELEGRAM KANALLARDAN SIGNALLAR]:
        {tg_signals}
        
        Sening vazifang eng muhimlarini saralash va qisqa "Alpha" (insider ma'lumot) berishdir.
        """
        
        try:
            # Send to the owner chat session directly or create a generic one
            # Assuming owner ID is accessible or we just use a generic model
            model = self.ai.chat_sessions.get(f"{self.ai.logger.get_logs_path()}_owner") 
            if not model:
                # Create a temporary session if not found
                import google.generativeai as genai
                temp_model = genai.GenerativeModel("gemini-flash-latest")
                response = temp_model.generate_content(prompt)
            else:
                response = model.send_message(prompt)
                
            return response.text
        except Exception as e:
            logger.error(f"Intelligence synthesis failed: {e}")
            return "Intelligence tahlilida xatolik yuz berdi."
