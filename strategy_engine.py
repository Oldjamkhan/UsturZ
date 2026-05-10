import os
import json
import logging
from pypdf import PdfReader
import google.generativeai as genai
from config import Config

logger = logging.getLogger(__name__)

class StrategyEngine:
    def __init__(self, vault_path, index_path):
        self.vault_path = vault_path
        self.index_path = index_path
        self.strategies = []
        
        if not os.path.exists(self.vault_path):
            os.makedirs(self.vault_path, exist_ok=True)

    def load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.strategies = json.load(f)
            except Exception as e:
                logger.error(f"Error loading strategy index: {e}")
                self.strategies = []
        else:
            self.strategies = []

    def build_index(self):
        logger.info("Building Strategy Index...")
        new_strategies = []
        
        for file_name in os.listdir(self.vault_path):
            path = os.path.join(self.vault_path, file_name)
            content = ""
            
            if file_name.endswith('.txt'):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif file_name.endswith('.pdf'):
                try:
                    reader = PdfReader(path)
                    for page in reader.pages:
                        content += page.extract_text()
                except Exception as e:
                    logger.error(f"Error reading PDF {file_name}: {e}")
                    continue
            else:
                continue
            
            if content:
                strategy = self._parse_strategy(content)
                if strategy:
                    strategy['file_name'] = file_name
                    new_strategies.append(strategy)
        
        self.strategies = new_strategies
        self._save_index()
        return len(self.strategies)

    def _parse_strategy(self, content):
        """Use Gemini to extract structured strategy info."""
        prompt = f"""
        Extract trading strategy details from the following text and return ONLY a JSON object.
        JSON format:
        {{
            "name": "strategiya nomi",
            "type": "scalping/trend/swing",
            "indicators": ["indicator1", "indicator2"],
            "rules": "kirish/chiqish qoidalari",
            "timeframe": "1h/4h/1d"
        }}
        
        TEXT:
        {content[:4000]}
        """
        
        try:
            model = genai.GenerativeModel("gemini-flash-latest")
            response = model.generate_content(prompt)
            json_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(json_text)
        except Exception as e:
            logger.error(f"Error parsing strategy with Gemini: {e}")
            return None

    def _save_index(self):
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.strategies, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving strategy index: {e}")

    def get_all_strategies(self):
        if not self.strategies:
            self.load_index()
        return self.strategies

    def get_strategy_detail(self, name):
        if not self.strategies:
            self.load_index()
        for s in self.strategies:
            if s['name'].lower() == name.lower():
                return s
        return None
