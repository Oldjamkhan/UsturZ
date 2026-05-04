import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

if not api_id or not api_hash:
    print("XATOLIK: .env faylida TELEGRAM_API_ID yoki TELEGRAM_API_HASH topilmadi.")
    print("Iltimos, my.telegram.org saytidan olib, .env fayliga kiriting.")
    exit(1)

client = TelegramClient('usturz_session', int(api_id), api_hash)

async def main():
    print("Telegram akkauntiga ulanilmoqda...")
    await client.start()
    print("\nMUVAFFAQIYATLI! Telegram akkauntiga ulandingiz.")
    print("Endi papkada 'usturz_session.session' nomli fayl paydo bo'ldi.")
    print("Bu faylni GitHub'ga push qilsangiz, Render serveri parolsiz to'g'ridan-to'g'ri ulanadi!")
    
    me = await client.get_me()
    print(f"Profil: {me.first_name} (@{me.username})")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
