import logging
import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

logger = logging.getLogger(__name__)

class TelegramIntelligence:
    def __init__(self, api_id: int = None, api_hash: str = None, phone: str = None):
        self.api_id = api_id or os.getenv("TELEGRAM_API_ID")
        self.api_hash = api_hash or os.getenv("TELEGRAM_API_HASH")
        self.phone = phone or os.getenv("TELEGRAM_PHONE")
        self.client = None
        
        if self.api_id and self.api_hash:
            self.client = TelegramClient('usturz_session', self.api_id, self.api_hash)
            logger.info("TelegramIntelligence initialized. Waiting for login/start.")
        else:
            logger.warning("TELEGRAM_API_ID or TELEGRAM_API_HASH missing. Intelligence module disabled.")

    async def start(self):
        if not self.client:
            return
            
        await self.client.connect()
        if not await self.client.is_user_authorized():
            if self.phone:
                try:
                    await self.client.send_code_request(self.phone)
                    logger.info(f"Code sent to {self.phone}. Please complete login in a separate script first.")
                except Exception as e:
                    logger.error(f"Error sending auth code: {e}")
            else:
                logger.error("Phone number not provided for Telegram login.")

    async def get_recent_messages(self, channel_username: str, limit: int = 10):
        if not self.client or not await self.client.is_user_authorized():
            return []
            
        messages = []
        try:
            async for message in self.client.iter_messages(channel_username, limit=limit):
                if message.text:
                    messages.append(message.text)
            return messages
        except Exception as e:
            logger.error(f"Error reading channel {channel_username}: {e}")
            return []

    async def monitor_channels(self, channels: list):
        # A simple method to pull the latest info from a list of channels
        all_signals = {}
        for ch in channels:
            msgs = await self.get_recent_messages(ch, limit=5)
            if msgs:
                all_signals[ch] = msgs
        return all_signals
