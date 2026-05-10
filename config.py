import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Bot identity
    BOT_NAME = "UsturZ"
    BOT_VERSION = "3.0"

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OWNER_ID = os.getenv("OWNER_ID")
    PAPER_TRADE = os.getenv("PAPER_TRADE", "true") == "true"
    
    # Secret keywords for 'Digital Twin' activation
    SECRET_KEYWORDS = ["ukam", "bratello"]
    
    # Render/Server support
    IS_SERVER = os.getenv("RENDER") == "true" or os.getenv("SERVER_MODE") == "true"
    
    # Paths
    ENERGY_VAULT_PATH = os.getenv('ENERGY_VAULT_PATH', "./UsturZ_Brain/Energy_Vault")
    BOOKS_VAULT_PATH = os.getenv('BOOKS_PATH', "./books")
    BRAIN_DIR = os.getenv('BRAIN_DIR', "./UsturZ_Brain")

    GRAPH_PATH = os.path.join(BRAIN_DIR, "graph_data.json")
    BOOKS_INDEX_PATH = os.path.join(BRAIN_DIR, "books_index.json")
    VISION_INDEX_PATH = os.path.join(BRAIN_DIR, "vision_index.json")
    DRAFTS_PATH = os.path.join(BRAIN_DIR, "Drafts")

    # Logging configuration
    LOG_LEVEL = logging.INFO
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN not found in environment")
        if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            logging.warning("GEMINI_API_KEY is not set or using placeholder. AI features will be disabled.")
