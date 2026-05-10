import google.generativeai as genai
from config import Config
import logging
from memory_engine import MemoryEngine
from energy_expert import EnergyExpert
from memory_graph import MemoryGraph
from scientific_writer import ScientificWriter
from math_engine import MathEngine
from chat_logger import ChatLogger
from book_vault import BookVault
from vision_vault import VisionVault
from binance_engine import BinanceEngine
from risk_manager import RiskManager
from strategy_engine import StrategyEngine
import re

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self):
        self.vault_path = Config.ENERGY_VAULT_PATH
        self.drafts_path = Config.DRAFTS_PATH
        self.graph_path = Config.GRAPH_PATH
        
        self.memory = MemoryEngine(self.vault_path)
        self.graph = MemoryGraph(self.vault_path, self.graph_path)
        self.writer = ScientificWriter(self.drafts_path)
        self.math = MathEngine()
        self.expert = EnergyExpert()
        self.logger = ChatLogger()
        
        # Initialize BookVault for deep knowledge from D:\1.book
        self.book_vault = BookVault(
            books_path=Config.BOOKS_VAULT_PATH,
            index_path=Config.BOOKS_INDEX_PATH,
            max_pages=10
        )
        
        # Initialize VisionVault for reading image folders
        self.vision_vault = VisionVault(
            index_path=Config.VISION_INDEX_PATH
        )
        
        # Initialize Trading Engines
        self.binance = BinanceEngine()
        self.risk = RiskManager()
        self.strategy_engine = StrategyEngine(
            vault_path=Config.TRADING_VAULT_PATH,
            index_path=Config.STRATEGY_INDEX_PATH
        )
        
        if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            self.model_owner = None
            logger.error("AIEngine: GEMINI_API_KEY is missing!")
            return
            
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Build knowledge graph on startup
        self.graph.scan_and_build()
        
        # Build book index if needed (runs in background-friendly way)
        if self.book_vault.needs_rebuild():
            logger.info("UsturZ: Building BookVault index for the first time...")
            self.book_vault.build_full_index()
        else:
            logger.info(f"UsturZ: BookVault loaded with {self.book_vault.index.get('total_files', 0)} files")
        
        # Build strategy index
        if not os.path.exists(Config.STRATEGY_INDEX_PATH):
            logger.info("UsturZ: Building Strategy index...")
            self.strategy_engine.build_index()
        else:
            self.strategy_engine.load_index()
            
        self.chat_sessions = {}

    async def get_response(self, user_id: int, message_text: str, username: str = "Unknown", is_owner: bool = False, image_data=None):
        """Advanced Autonomous Response Generator with deep book knowledge."""
        # Log incoming user message
        self.logger.log_message(user_id, username, "USER", message_text if message_text else "[IMAGE/FILE]")
        
        context = ""
        mem_context = self.memory.get_context()
        
        # Get relevant book knowledge based on user's query
        book_context = ""
        vision_context = ""
        if message_text:
            book_context = self.book_vault.get_context_for_query(message_text)
            vision_context = self.vision_vault.get_vision_context(message_text)
        if not book_context or len(book_context) < 50:
            book_context = self.book_vault.get_full_brain_context()
        
        if is_owner:
            graph_summary = self.graph.get_graph_summary()
            
            # Combine all context
            context = f"DRAFT ANALYTICS AND GRAPH:\n{graph_summary[:1000]}\n\nRECENT DOCUMENTS:\n{mem_context}\n{vision_context}"
            system_instruction = self.expert.get_expert_prompt(context, book_context)
            
            # Special instruction for Level 2 autonomy
            system_instruction += """
            SENING IMKONIYATLARING (LEVEL 3 — USTOZ MODE):
            - Sen 'Drafts' papkasiga yangi maqolalar yozib saqlay olasan.
            - Sen murakkab muhandislik hisob-kitoblarini bajara olasan.
            - Sen Binance orqali kriptovalyuta savdosini va risk menejmentini qila olasan.
            - Sen 1700+ ta kitob va hujjatdan bilim olasan va dalillar keltirib javob berasan.
            - Sen energetika, gidravlika, atom energetikasi, fizika, iqtisodiyot bo'yicha chuqur tahlil qilasan.
            
            Agar foydalanuvchi maqola yozishni so'rasa, sening javobingda 'ACTION: WRITE_DRAFT' kalit so'zi va tahlil bo'lishi shart.
            Agar hisoblash so'ralsa, 'ACTION: MATH_CALC' kalit so'zini ishlat.
            Agar kitoblardan qidirish so'ralsa, 'ACTION: BOOK_SEARCH' kalit so'zini ishlat.
            Agar rasmli papkani skanerlashni so'rasa, 'ACTION: SCAN_VISION_FOLDER <papka_manzili>' formatida javob ber.
            Agar foydalanuvchi biror koin narxini so'rasa yoki savdo qilish kerak bo'lsa, 'ACTION: TRADE <SYMBOL> <BUY/SELL>' kalit so'zidan foydalan (Masalan: ACTION: TRADE BTCUSDT BUY).
            """
        else:
            system_instruction = f"""
            Sening isming **UsturZ**. Sen Jamshidbek Olimovning rasmiy virtual yordamchisisan.
            Sen 1700+ ta ilmiy kitob va hujjat bilan qurollangansen.
            Muloqotda samimiy va professional bo'l, lekin haddan tashqari maqtovlardan qoch.
            
            **MUHIM FAKT:**
            Jamshidbek Olimov hech qanday treyding akademiya rahbari EMAS. U treyding va kriptovalyutani mustaqil o'rganadi. 
            Ma'lumotlar bazasidagi kitoblar faqat o'quv qo'llanmalari hisoblanadi.
            
            **JAMSHIDBEK HAQIDA MA'LUMOTLAR:**
            {mem_context[:2000]}
            
            **KUTUBXONA BILIMI:**
            {book_context[:1500]}
            
            **RASMLAR XOTIRASI:**
            {vision_context}
            
            Foydalanuvchilar Jamshidbekning yutuqlari yoki loyihalari haqida so'rashsa, faqat ma'lumotlar bazasidagi faktlarga tayan. 
            Uni yosh tadqiqotchi va muhandis sifatida taqdim et.
            Agar ilmiy savol berilsa, kutubxonadagi tegishli manbalardan dalillar keltir.
            """

        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=system_instruction
        )
        
        session_key = f"{user_id}_{'owner' if is_owner else 'public'}"
        if session_key not in self.chat_sessions:
            self.chat_sessions[session_key] = model.start_chat(history=[])
            
        try:
            content = []
            if message_text:
                content.append(message_text)
            if image_data:
                # image_data expected to be a dict with 'mime_type' and 'data' (bytes)
                content.append(image_data)
                
            response = self.chat_sessions[session_key].send_message(content)
            response_text = response.text
            
            # Execute Trade Action if present
            if "ACTION: TRADE" in response_text:
                match = re.search(r'ACTION: TRADE\s+([A-Za-z0-9]+)\s+(BUY|SELL)', response_text, re.IGNORECASE)
                if match:
                    symbol, side = match.groups()
                    symbol = symbol.upper()
                    side = side.upper()
                    
                    price = self.binance.get_price(symbol)
                    bal = self.binance.get_balance("USDT")
                    
                    response_text += f"\n\n🤖 **[USTURZ SYSTEM]**: \n- {symbol} joriy narxi: {price}$\n- Balans: {bal} USDT\n- Risk Manager orqali tekshirilmoqda..."
            
            # Log bot response
            self.logger.log_message(user_id, username, "BOT", response_text)
            
            return response_text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            error_msg = "Xatolik yuz berdi. UsturZ hozir buni tuzatyapti!"
            self.logger.log_message(user_id, username, "BOT", f"ERROR: {e}")
            return error_msg
