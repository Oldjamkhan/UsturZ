import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from config import Config
from ai_engine import AIEngine
from unity_bridge import UnityBridge

# Configure logging
logging.basicConfig(level=Config.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AI Engine
ai_engine = AIEngine()

# Initialize Bot and Dispatcher
bot = Bot(token=Config.TELEGRAM_TOKEN)
dp = Dispatcher()

def build_callback(file_path):
    """Callback triggered by UnityBridge when a new build is detected."""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(bot.send_message(
            chat_id=Config.OWNER_ID, 
            text=f"🚀 **Bratello, yangi build tayyor!**\nFayl: `{os.path.basename(file_path)}`\nUni tekshirib ko'ramizmi?"
        ))
    except Exception as e:
        logger.error(f"Build callback error: {e}")

# Initialize Unity Bridge
unity_bridge = UnityBridge(Config.UNITY_BUILDS_PATH, build_callback)

@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    await message.answer(f"Sening Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    book_count = ai_engine.book_vault.index.get('total_files', 0)
    await message.answer(
        f"Assalomu alaykum! Men **{Config.BOT_NAME}** — Jamshidbek Olimovning rasmiy virtual yordamchisiman.\n\n"
        f"📚 Mening bilimlar bazamda **{book_count}+ ta ilmiy kitob va hujjat** mavjud.\n\n"
        "🔬 Energetika, gidravlika, atom energetikasi, muhandislik, iqtisodiyot va boshqa ko'plab sohalarda yordam bera olaman.\n\n"
        "Sizga qanday yordam kerak?",
        parse_mode="Markdown"
    )

@dp.message(Command("brain"))
async def cmd_brain(message: types.Message):
    """Show brain statistics — available to everyone."""
    overview = ai_engine.book_vault.get_category_overview()
    await message.answer(
        f"🧠 **{Config.BOT_NAME} — Brain Status**\n\n{overview}",
        parse_mode="Markdown"
    )

@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    """Search the book vault for specific topics."""
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.answer("ℹ️ Qidirish uchun so'z yozing. Masalan: `/search gidravlika`", parse_mode="Markdown")
        return
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    results = ai_engine.book_vault.search(query, max_results=5)
    await message.answer(
        f"🔍 **Qidiruv: \"{query}\"**\n\n{results}",
        parse_mode="Markdown"
    )

@dp.message(Command("rebuild"))
async def cmd_rebuild(message: types.Message):
    """Rebuild the book index — owner only."""
    if str(message.from_user.id) != str(Config.OWNER_ID):
        await message.answer("❌ Bu buyruq faqat bot egasi uchun ochiq.")
        return
    
    await message.answer("🔄 Kutubxona indeksi qayta qurilmoqda... Bu biroz vaqt olishi mumkin.")
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    ai_engine.book_vault.build_full_index()
    overview = ai_engine.book_vault.get_category_overview()
    await message.answer(f"✅ Indeks tayyor!\n\n{overview}", parse_mode="Markdown")

@dp.message(Command("logs"))
async def cmd_logs(message: types.Message):
    if str(message.from_user.id) != str(Config.OWNER_ID):
        await message.answer("❌ Bu buyruq faqat bot egasi uchun ochiq.")
        return
        
    log_file_path = ai_engine.logger.get_logs_path()
    if os.path.exists(log_file_path):
        await message.answer_document(
            FSInputFile(log_file_path),
            caption=f"📊 **{Config.BOT_NAME} Chat Loglari**"
        )
    else:
        await message.answer("ℹ️ Hozircha loglar mavjud emas.")

async def process_autonomous_actions(message: types.Message, response_text: str):
    """Handles Level 3 Autonomous actions triggered by the AI."""
    if "ACTION: WRITE_DRAFT" in response_text:
        title = "Gidravlika_va_Energetika_Draft"
        content_blocks = {
            "topic": "Gidravlika tizimlari",
            "focus": "Suyuqlik oqimi va energiya yo'qotishlari",
            "body": "Suyuqlikning quvurlardagi harakati davomida gidravlik qarshiliklar sababli kinetik energiya issiqlikka aylanadi...",
            "data_point": "Ishqalanish koeffitsienti 0.025 ga teng",
            "thesis": "Energiya samaradorligini oshirish",
            "summary": "Energetika analogiyasi gidravlik yo'qotishlarni kamaytirishda xizmat qiladi",
            "prospect": "Yuqori samarali gidravlik nasoslar"
        }
        
        file_path = ai_engine.writer.create_draft(title, content_blocks)
        if file_path:
            clean_response = response_text.replace("ACTION: WRITE_DRAFT", "").strip()
            await message.answer(f"{clean_response}\n\n📝 **Bratello, maqola qoralasini tayyorlab, 'Drafts' papkasiga tashlab qo'ydim.**\nLink: `{file_path}`")
            return

    if "ACTION: BOOK_SEARCH" in response_text:
        # Extract search query from response
        clean_response = response_text.replace("ACTION: BOOK_SEARCH", "").strip()
        try:
            await message.answer(clean_response, parse_mode="Markdown")
        except:
            await message.answer(clean_response) # Fallback if markdown is broken
        return

    if "ACTION: SCAN_VISION_FOLDER" in response_text:
        # Extract folder path
        import re
        match = re.search(r"ACTION: SCAN_VISION_FOLDER\s+([^\n]+)", response_text)
        if match:
            folder_path = match.group(1).strip()
            clean_response = response_text.replace(match.group(0), "").strip()
            await message.answer(f"{clean_response}\n\n🔍 **VisionVault:** `{folder_path}` papkasidagi rasmlarni skanerlashni boshladim... Bunga biroz vaqt ketishi mumkin.")
            
            # Run scan in background to not block the bot
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, ai_engine.vision_vault.scan_folder, folder_path)
            
            await message.answer(f"✅ **VisionVault Xabari:**\n{result}", parse_mode="Markdown")
            return
            
    try:
        await message.answer(response_text, parse_mode="Markdown")
    except:
        await message.answer(response_text) # Fallback if markdown is broken

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    image_data = {"mime_type": "image/jpeg", "data": file_bytes.read()}
    
    text = message.caption or ""
    is_owner = ("ukam" in text.lower() and "bratello" in text.lower())
    response_text = await ai_engine.get_response(
        message.from_user.id, 
        message.caption, 
        username=message.from_user.full_name,
        is_owner=is_owner, 
        image_data=image_data
    )
    await process_autonomous_actions(message, response_text)

@dp.message()
async def handle_message(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    text = message.text.lower()
    is_owner = ("ukam" in text and "bratello" in text)
    response_text = await ai_engine.get_response(
        message.from_user.id, 
        message.text, 
        username=message.from_user.full_name,
        is_owner=is_owner
    )
    await process_autonomous_actions(message, response_text)

async def health_check(request):
    return aiohttp.web.Response(text="UsturZ Digital Twin is running smoothly!")

async def start_web_server():
    app = aiohttp.web.Application()
    app.router.add_get('/', health_check)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Web server started on port {port} for Render health checks.")

async def main():
    logger.info(f"Starting {Config.BOT_NAME} v{Config.BOT_VERSION} (Level 3 — UsturZ Mode)...")
    if not Config.IS_SERVER:
        unity_bridge.start()
        
    try:
        # Start dummy web server if running on a cloud service like Render
        if Config.IS_SERVER:
            import aiohttp.web
            await start_web_server()
            
        await dp.start_polling(bot)
    finally:
        if not Config.IS_SERVER:
            unity_bridge.stop()

if __name__ == "__main__":
    import aiohttp.web
    
    # Ensure data directories exist for server mode
    if Config.IS_SERVER:
        for path in [Config.ENERGY_VAULT_PATH, Config.BOOKS_VAULT_PATH, Config.BRAIN_DIR, Config.UNITY_BUILDS_PATH, Config.DRAFTS_PATH]:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created/Verified directory: {path}")

    asyncio.run(main())
