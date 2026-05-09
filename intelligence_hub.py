import logging
import asyncio
import sqlite3
import os
import json
from datetime import datetime
from perplexity_news import PerplexityNews
from telegram_intelligence import TelegramIntelligence
from config import Config

logger = logging.getLogger(__name__)

class IntelligenceHub:
    def __init__(self, ai_engine):
        self.ai = ai_engine
        self.perplexity = PerplexityNews()
        self.telegram = TelegramIntelligence()
        self.db_path = os.path.join(Config.BRAIN_DIR, "intelligence_db.sqlite")
        
        # Initialize Database
        self._init_db()
        
        # Add channels to monitor
        self.target_channels = ["@whale_alert", "@CryptoBanterGroup"] 
        
        logger.info("IntelligenceHub v2.0 initialized.")

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS intelligence 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          source TEXT, 
                          content TEXT, 
                          category TEXT, 
                          relevance REAL, 
                          urgency TEXT, 
                          summary TEXT, 
                          processed INTEGER DEFAULT 0,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize Intelligence DB: {e}")

    async def process_incoming_item(self, content: str, source: str = "email"):
        """Classify and process incoming intelligence items (emails, alerts, etc.)"""
        prompt = f"""
        Quyidagi ma'lumotni (email/xabar) tahlil qil va JSON formatida qaytar.
        
        KATEGORIYALAR:
        1. "uzbek_politics" — O'zbekiston siyosati
        2. "energy" — Energetika (atom, neft, gaz, qayta tiklanuvchi)
        3. "global_politics" — Jahon siyosati, geosiyosat
        4. "finance_crypto" — Moliya, kripto, forex
        5. "academic" — O'qish, fan, texnologiya
        
        JSON FORMATI:
        {{
            "category": "kategoriya_nomi",
            "relevance": 0.0-1.0 (float),
            "urgency": "low" / "medium" / "high",
            "summary": "2 jumlada o'zbek tilida xulosa"
        }}
        
        MA'LUMOT:
        {content}
        """
        
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-flash-latest")
            response = model.generate_content(prompt)
            
            # Clean JSON response
            json_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_text)
            
            # Store in DB
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO intelligence (source, content, category, relevance, urgency, summary) VALUES (?, ?, ?, ?, ?, ?)",
                      (source, content, data['category'], data['relevance'], data['urgency'], data['summary']))
            conn.commit()
            conn.close()
            
            # Handle Actions based on Urgency
            if data['urgency'] == "high":
                await self.send_immediate_alert(data, source)
                
            return data
        except Exception as e:
            logger.error(f"Error processing intelligence item: {e}")
            return None

    async def send_immediate_alert(self, data, source):
        """Send high urgency alerts to Telegram immediately."""
        from aiogram import Bot
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        text = f"🚨 **SHOSHILINCH XABAR ({source.upper()})**\n\n" \
               f"📂 **Kategoriya:** #{data['category']}\n" \
               f"🎯 **Dolzarblik:** {data['relevance']*100}%\n\n" \
               f"📝 **Xulosa:** {data['summary']}"
        try:
            await bot.send_message(chat_id=Config.OWNER_ID, text=text, parse_mode="Markdown")
        finally:
            await bot.session.close()

    async def generate_morning_report(self):
        """Generates the 09:00 Morning Report as requested."""
        logger.info("Generating Morning Report...")
        
        # 1. Get Market Info
        btc_price = self.ai.binance.get_price("BTCUSDT")
        
        # 2. Get latest news per category from DB
        categories = ["uzbek_politics", "energy", "global_politics", "finance_crypto", "academic"]
        report_data = {}
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        for cat in categories:
            c.execute("SELECT summary FROM intelligence WHERE category = ? ORDER BY timestamp DESC LIMIT 2", (cat,))
            rows = c.fetchall()
            report_data[cat] = [r[0] for r in rows] if rows else ["Yangi ma'lumot yo'q."]
        conn.close()

        # 3. Get Book Recommendation (Academic/Energy related)
        book_rec = self.ai.book_vault.get_context_for_query("Bugun o'qish uchun tavsiya: muhandislik yoki energetika")
        if len(book_rec) > 500: book_rec = book_rec[:500] + "..."

        now = datetime.now().strftime("%d-%m-%Y")
        report = f"📊 **USTURZ ERTALABKI HISOBOT — {now} 09:00**\n\n"
        
        report += f"🇺🇿 **O'ZBEKISTON:**\n" + "\n".join([f"- {s}" for s in report_data["uzbek_politics"]]) + "\n\n"
        report += f"⚡ **ENERGETIKA:**\n" + "\n".join([f"- {s}" for s in report_data["energy"]]) + "\n\n"
        report += f"🌍 **GLOBAL SIYOSAT:**\n" + "\n".join([f"- {s}" for s in report_data["global_politics"]]) + "\n\n"
        report += f"💹 **BOZOR:**\n- BTC: ${btc_price:,}\n- Savdo holati: Tizim aktiv holatda.\n\n"
        report += f"📚 **BUGUNGI O'QUV TAVSIYA:**\n{book_rec}"
        
        return report

    async def generate_evening_report(self):
        """Generates the 20:00 Evening Report for 'medium' urgency items."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Fetch medium urgency items that haven't been reported in an evening report yet
        # For simplicity, we just fetch today's medium items
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT category, summary FROM intelligence WHERE urgency = 'medium' AND timestamp LIKE ?", (f"{today}%",))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return "🌙 **Kechki hisobot:** Bugun o'rtacha dolzarblikdagi yangi ma'lumotlar yo'q."
            
        report = "🌙 **USTURZ KECHKI HISOBOT — 20:00**\n\n"
        for cat, summary in rows:
            report += f"🔹 [#{cat}] {summary}\n"
            
        return report

    async def get_daily_synthesis(self):
        """Legacy synthesis method, can be kept or integrated."""
        news = self.perplexity.get_market_news()
        return f"Bozor yangiliklari:\n{news}"
