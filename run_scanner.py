import os
import sys

# Change working directory to the project root to load modules correctly
os.chdir(r"c:\Users\User\.gemini\abdumajidxon-ai")
sys.path.append(r"c:\Users\User\.gemini\abdumajidxon-ai")

from ai_engine import AIEngine
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_scan():
    logger.info("Initializing AIEngine for scanning...")
    engine = AIEngine()
    logger.info(r"Starting scan for D:\1.Book\1.Rasmlar (This will take ~50 mins for 200 files)...")
    res = engine.vision_vault.scan_folder(r"D:\1.Book\1.Rasmlar")
    logger.info(f"Scan Result: {res}")

if __name__ == "__main__":
    run_scan()
