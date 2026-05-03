import os
import json
import logging
import hashlib
import google.generativeai as genai
from config import Config

logger = logging.getLogger(__name__)

class VisionVault:
    """
    VisionVault — UsturZ uchun rasmlarni (sxemalar, chizmalar, konspektlar) 
    o'qib tushunuvchi va xotiraga oluvchi tizim.
    Gemini Vision modelidan foydalanib rasmlardagi matn va chizmalarni indekslaydi.
    """
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.index = {
            "total_images": 0,
            "images": {}
        }
        
        # Ensure API key is set for Vision
        if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.vision_model = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.vision_model = None
            
        self._load_index()

    def _load_index(self):
        """Load existing image index from disk."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
                logger.info(f"VisionVault: Loaded index with {self.index.get('total_images', 0)} images")
            except Exception as e:
                logger.error(f"VisionVault: Error loading index: {e}")

    def _save_index(self):
        """Save image index to disk."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
            logger.info(f"VisionVault: Index saved ({self.index['total_images']} images)")
        except Exception as e:
            logger.error(f"VisionVault: Error saving index: {e}")
            
    def _file_hash(self, filepath: str) -> str:
        try:
            size = os.path.getsize(filepath)
            return hashlib.md5(f"{os.path.basename(filepath)}_{size}".encode()).hexdigest()[:12]
        except:
            return ""

    def process_image(self, filepath: str) -> str:
        """Uploads and analyzes an image using Gemini Vision."""
        if not self.vision_model:
            return "Vision modeli ishlamayapti (API kalit topilmadi)."
            
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Upload image using Gemini File API for processing
                img_file = genai.upload_file(path=filepath)
                
                prompt = (
                    "Ushbu rasmda nimalar tasvirlanganini batafsil tushuntirib ber. "
                    "Agar rasmda matn (yozuv) bo'lsa, uni to'liq o'qib ber. "
                    "Agar bu muhandislik sxemasi, chizma yoki grafik bo'lsa, uning "
                    "tuzilishini va nima maqsadda ishlatilishini ilmiy tahlil qil. "
                    "Javobni o'zbek tilida yoz."
                )
                
                response = self.vision_model.generate_content([img_file, prompt])
                
                # Clean up the uploaded file to save space
                genai.delete_file(img_file.name)
                
                return response.text
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg and attempt < max_retries - 1:
                    logger.warning(f"Quota exceeded. Retrying {filepath} in 35 seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(35)
                    continue
                logger.error(f"Vision error processing {filepath}: {e}")
                return f"Xatolik yuz berdi: {e}"

    def scan_folder(self, folder_path: str):
        """Scans a folder for images and indexes their content."""
        if not os.path.exists(folder_path):
            return f"Papka topilmadi: {folder_path}"
            
        logger.info(f"VisionVault: Scanning folder {folder_path}...")
        
        added_count = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    filepath = os.path.join(root, file)
                    file_hash = self._file_hash(filepath)
                    
                    # Skip if already indexed
                    if file_hash in self.index["images"]:
                        continue
                        
                    logger.info(f"VisionVault: Processing new image {file}...")
                    description = self.process_image(filepath)
                    
                    if not description.startswith("Xatolik"):
                        self.index["images"][file_hash] = {
                            "filename": file,
                            "filepath": filepath,
                            "description": description
                        }
                        added_count += 1
                        self._save_index() # Save progressively
                        
                    # Respect Gemini free tier rate limits (15 RPM)
                    import time
                    time.sleep(15)
                        
        self.index["total_images"] = len(self.index["images"])
        self._save_index()
        return f"Skanerlash yakunlandi. {added_count} ta yangi rasm o'qilib, xotiraga yozildi."

    def search_images(self, query: str, max_results: int = 3) -> str:
        """Searches through indexed images based on query."""
        if not self.index.get("images"):
            return "VisionVault xotirasida rasmlar yo'q."
            
        query_lower = query.lower()
        results = []
        
        for file_hash, info in self.index["images"].items():
            score = 0
            desc = info.get("description", "").lower()
            
            for word in query_lower.split():
                if len(word) > 2 and word in desc:
                    score += 1
                    
            if score > 0:
                results.append((info, score))
                
        results.sort(key=lambda x: x[1], reverse=True)
        
        if not results:
            return "Siz so'ragan mavzuda rasmlar topilmadi."
            
        output = []
        for info, score in results[:max_results]:
            filename = info.get("filename", "Noma'lum rasm")
            path = info.get("filepath", "")
            desc = info.get("description", "")[:300] + "..."
            output.append(f"🖼 **Rasm:** {filename}\n📁 **Manzil:** `{path}`\n📝 **Tahlil:** {desc}\n")
            
        return "\n".join(output)

    def get_vision_context(self, query: str) -> str:
        """Returns vision context for AI prompt injection."""
        results = self.search_images(query, max_results=2)
        if "topilmadi" in results or "yo'q" in results:
            return ""
        return f"\nRASMLAR XOTIRASI (VisionVault):\n{results}\n"
