import logging
import requests
import os

logger = logging.getLogger(__name__)

class PerplexityNews:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

    def get_market_news(self, query: str = "Crypto market sentiment and major news today") -> str:
        if not self.api_key or self.api_key == "YOUR_PERPLEXITY_API_KEY_HERE":
            logger.warning("Perplexity API Key missing. Returning mock news.")
            return "Bozor holati stabil, BTC $65K atrofida. ETF yangiliklari kutilmoqda."
            
        payload = {
            "model": "llama-3-sonar-large-32k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional financial news summarizer. Provide a highly concise summary of the most critical current market events."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 500,
            "temperature": 0.2
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                logger.error(f"Perplexity API Error: {response.text}")
                return "Yangiliklarni olishda xatolik yuz berdi."
        except Exception as e:
            logger.error(f"Failed to fetch from Perplexity: {e}")
            return "Internetga ulanishda xatolik."
