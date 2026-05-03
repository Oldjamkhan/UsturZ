"""
BookVault — UsturZ uchun chuqur bilimlar bazasi.
D:\1.book papkasidagi 1700+ faylni indekslaydi, kategoriyalaydi va qidiradi.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from memory_engine import MemoryEngine

logger = logging.getLogger(__name__)


class BookVault:
    """Deep knowledge indexing and search system for 1700+ academic files."""

    # Topic categories with keywords for classification
    CATEGORIES = {
        "Energetika": [
            "энерг", "energetik", "energiya", "electr", "электр", "трансформатор",
            "transformer", "генератор", "generator", "турбин", "turbina", "quvvat",
            "power", "kuchlanish", "voltage", "tok", "emt", "линия", "liniya",
            "подстанц", "подстанция", "relay", "реле", "himoya", "защит",
            "таъминот", "ta'minot", "samaradorlik", "efficiency", "электромонтаж",
        ],
        "Atom_Energetikasi": [
            "атом", "atom", "магатэ", "magate", "ядер", "nuclear", "узатом",
            "uzatom", "аэс", "aes", "радиац", "radiation", "реактор", "reactor",
        ],
        "Gidravlika": [
            "гидравл", "gidravlik", "hydraul", "suv", "насос", "nasos", "pump",
            "quvur", "труб", "pipe", "давлен", "bosim", "pressure", "oqim", "flow",
            "suyuqlik", "жидкост",
        ],
        "Treyding_Moliya": [
            "trading", "treyding", "forex", "valyuta", "market", "stock", "birja",
            "indikator", "indicator", "narx", "price", "sham", "candle", "chart",
            "crypto", "bitcoin", "treyder", "trader", "ict", "cfa", "frm",
            "invest", "profit", "strategy", "strategiya",
        ],
        "Iqtisodiyot": [
            "iqtisod", "экономик", "econom", "keyns", "макро", "микро", "moliya",
            "финанс", "finance", "бозор", "bozor", "marketing", "менеджмент",
            "management", "siyosat", "policy",
        ],
        "Fizika_Matematika": [
            "физик", "fizika", "physics", "математик", "matematik", "math",
            "formula", "уравнен", "теорем", "theorem", "hawking", "квант",
            "quantum", "механик", "mexanika", "mechanics",
        ],
        "Falsafa_Gumanitar": [
            "фалсафа", "falsafa", "философ", "philos", "тарих", "tarix",
            "history", "маданият", "madaniyat", "culture", "адабиёт", "adabiyot",
        ],
        "Texnika_Muhandislik": [
            "техник", "texnika", "technical", "стандарт", "standart", "standard",
            "гост", "gost", "метролог", "metrologiya", "metrology", "чертёж",
            "chizma", "drawing", "cad", "autocad", "конструкц", "konstruksiya",
            "корхона", "korxona", "enterprise", "саноат", "sanoat", "industrial",
        ],
        "Tibbiyot": [
            "тиб", "tibbiyot", "медицин", "medicine", "ёрдам", "yordam",
            "health", "соғлиқ", "sog'liq",
        ],
        "IT_Dasturlash": [
            "unity", "script", "code", "program", "python", "c#", "java",
            "dastur", "software", "web", "html", "database",
        ],
        "Neft_Gaz": [
            "нефт", "neft", "газ", "gaz", "oil", "petroleum", "лукойл",
            "lukoil", "минбулак", "бурен", "бурғи", "burg'i", "drilling",
        ],
    }

    # Supported file extensions for text extraction
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.pptx', '.rtf', '.epub'}

    def __init__(self, books_path: str, index_path: str, max_pages: int = 10):
        self.books_path = books_path
        self.index_path = index_path
        self.max_pages = max_pages
        self.memory = MemoryEngine(books_path)
        self.index = {
            "total_files": 0,
            "categories": {},
            "files": {},
            "category_summaries": {},
        }
        self._load_index()

    def _load_index(self):
        """Load existing index from disk if available."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
                logger.info(f"BookVault: Loaded index with {self.index.get('total_files', 0)} files")
            except Exception as e:
                logger.error(f"BookVault: Error loading index: {e}")

    def _save_index(self):
        """Save index to disk."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
            logger.info(f"BookVault: Index saved ({self.index['total_files']} files)")
        except Exception as e:
            logger.error(f"BookVault: Error saving index: {e}")

    def _file_hash(self, filepath: str) -> str:
        """Quick hash based on file name + size for change detection."""
        try:
            size = os.path.getsize(filepath)
            return hashlib.md5(f"{os.path.basename(filepath)}_{size}".encode()).hexdigest()[:12]
        except:
            return ""

    def _classify_file(self, filename: str, content: str = "") -> list:
        """Classify a file into topic categories based on name and content."""
        categories = []
        search_text = (filename + " " + content[:2000]).lower()

        for category, keywords in self.CATEGORIES.items():
            score = sum(1 for kw in keywords if kw.lower() in search_text)
            if score >= 1:
                categories.append((category, score))

        # Sort by relevance score, return top 3
        categories.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in categories[:3]] if categories else ["Boshqa"]

    def _extract_deep_content(self, filepath: str) -> str:
        """Extract deeper content from a file (more pages than default)."""
        ext = Path(filepath).suffix.lower()
        content = ""

        try:
            if ext == '.pdf':
                content = self._extract_pdf_deep(filepath)
            elif ext == '.docx':
                content = self._extract_docx_deep(filepath)
            elif ext == '.txt':
                content = self._extract_txt(filepath)
            elif ext == '.pptx':
                content = self.memory.extract_text_from_pptx(filepath)
            elif ext == '.doc':
                content = self._extract_doc(filepath)
            elif ext == '.rtf':
                content = self._extract_rtf(filepath)
        except Exception as e:
            logger.debug(f"BookVault: Could not extract {filepath}: {e}")

        return content.strip()

    def _extract_pdf_deep(self, filepath: str) -> str:
        """Extract more pages from PDF for deeper understanding."""
        import pypdf
        text = ""
        try:
            with open(filepath, 'rb') as f:
                reader = pypdf.PdfReader(f)
                total_pages = len(reader.pages)
                # Read up to max_pages
                for i in range(min(total_pages, self.max_pages)):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.debug(f"PDF extract error: {e}")
        return text

    def _extract_docx_deep(self, filepath: str) -> str:
        """Extract more content from DOCX."""
        from docx import Document
        text = ""
        try:
            doc = Document(filepath)
            for para in doc.paragraphs[:100]:  # First 100 paragraphs
                text += para.text + "\n"
        except Exception as e:
            logger.debug(f"DOCX extract error: {e}")
        return text

    def _extract_txt(self, filepath: str) -> str:
        """Extract text from TXT files."""
        text = ""
        for encoding in ['utf-8', 'cp1251', 'latin-1']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    text = f.read(10000)  # First 10KB
                break
            except:
                continue
        return text

    def _extract_doc(self, filepath: str) -> str:
        """Try to extract from old .doc format."""
        # Limited support - try reading as binary text
        try:
            with open(filepath, 'rb') as f:
                raw = f.read(20000)
                # Try to extract readable text from binary
                text_parts = []
                current = ""
                for byte in raw:
                    if 32 <= byte <= 126 or byte in (10, 13):
                        current += chr(byte)
                    else:
                        if len(current) > 20:
                            text_parts.append(current)
                        current = ""
                return "\n".join(text_parts[:50])
        except:
            return ""

    def _extract_rtf(self, filepath: str) -> str:
        """Basic RTF text extraction."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)
                # Strip RTF commands (basic)
                import re
                text = re.sub(r'\\[a-z]+\d*\s?', ' ', content)
                text = re.sub(r'[{}]', '', text)
                return text[:5000]
        except:
            return ""

    def build_full_index(self):
        """Scan and index ALL files in the books folder. Run once on startup."""
        if not os.path.exists(self.books_path):
            logger.error(f"BookVault: Path not found: {self.books_path}")
            return

        logger.info(f"BookVault: Starting full index of {self.books_path}...")

        files = []
        for f in os.listdir(self.books_path):
            full_path = os.path.join(self.books_path, f)
            if os.path.isfile(full_path):
                files.append(f)

        self.index["total_files"] = len(files)
        self.index["categories"] = {}
        self.index["files"] = {}
        category_contents = {}

        for i, filename in enumerate(files):
            filepath = os.path.join(self.books_path, filename)
            ext = Path(filename).suffix.lower()
            file_hash = self._file_hash(filepath)

            # Skip unsupported files
            if ext not in self.SUPPORTED_EXTENSIONS:
                continue

            # Extract content
            content = self._extract_deep_content(filepath)
            if not content or len(content) < 30:
                # Even without content, classify by filename
                content = ""

            # Classify
            categories = self._classify_file(filename, content)

            # Create summary (first 500 chars)
            summary = content[:500].replace('\n', ' ').strip() if content else ""

            # Store file info
            self.index["files"][filename] = {
                "hash": file_hash,
                "ext": ext,
                "categories": categories,
                "summary": summary,
                "size": os.path.getsize(filepath),
            }

            # Aggregate by category
            for cat in categories:
                if cat not in self.index["categories"]:
                    self.index["categories"][cat] = []
                self.index["categories"][cat].append(filename)

                if cat not in category_contents:
                    category_contents[cat] = []
                if summary:
                    category_contents[cat].append(f"[{filename}]: {summary[:200]}")

            # Progress log every 100 files
            if (i + 1) % 100 == 0:
                logger.info(f"BookVault: Indexed {i + 1}/{len(files)} files...")

        # Build category summaries
        for cat, contents in category_contents.items():
            self.index["category_summaries"][cat] = "\n".join(contents[:30])

        self._save_index()
        logger.info(f"BookVault: Full index complete! {len(self.index['files'])} files in {len(self.index['categories'])} categories")

    def needs_rebuild(self) -> bool:
        """Check if index needs rebuilding."""
        if not self.index.get("files"):
            return True
        # Check if file count changed significantly
        try:
            current_count = len(os.listdir(self.books_path))
            indexed_count = self.index.get("total_files", 0)
            return abs(current_count - indexed_count) > 10
        except:
            return True

    def search(self, query: str, max_results: int = 5) -> str:
        """Search the book vault for relevant knowledge."""
        if not self.index.get("files"):
            return "BookVault indeksi hali qurilmagan."

        query_lower = query.lower()
        results = []

        for filename, info in self.index["files"].items():
            score = 0
            fname_lower = filename.lower()

            # Score based on query words in filename
            for word in query_lower.split():
                if len(word) > 2 and word in fname_lower:
                    score += 3
                if len(word) > 2 and info.get("summary", "") and word in info["summary"].lower():
                    score += 1

            if score > 0:
                results.append((filename, info, score))

        # Sort by score
        results.sort(key=lambda x: x[2], reverse=True)

        if not results:
            return self._search_by_category(query)

        output = []
        for filename, info, score in results[:max_results]:
            cats = ", ".join(info.get("categories", []))
            summary = info.get("summary", "")[:300]
            output.append(f"📚 **{filename}** [{cats}]\n{summary}\n")

        return "\n".join(output)

    def _search_by_category(self, query: str) -> str:
        """Fallback: search by category when direct search fails."""
        query_lower = query.lower()
        matched_categories = []

        for cat, keywords in self.CATEGORIES.items():
            if any(kw.lower() in query_lower for kw in keywords):
                matched_categories.append(cat)

        if not matched_categories:
            return "Bu mavzuda kitoblar topilmadi."

        output = []
        for cat in matched_categories[:2]:
            summary = self.index.get("category_summaries", {}).get(cat, "")
            file_count = len(self.index.get("categories", {}).get(cat, []))
            output.append(f"📂 **{cat}** ({file_count} ta fayl)\n{summary[:500]}\n")

        return "\n".join(output)

    def get_category_overview(self) -> str:
        """Get an overview of all categories and file counts."""
        if not self.index.get("categories"):
            return "Indeks bo'sh."

        lines = ["📊 **Kutubxona Statistikasi:**\n"]
        total = 0
        for cat, files in sorted(self.index["categories"].items(), key=lambda x: len(x[1]), reverse=True):
            count = len(files)
            total += count
            lines.append(f"  • {cat}: {count} ta fayl")

        lines.insert(1, f"  **Jami indekslangan:** {len(self.index.get('files', {}))} ta fayl\n")
        return "\n".join(lines)

    def get_context_for_query(self, query: str) -> str:
        """Get relevant book knowledge context for AI prompt enrichment."""
        search_results = self.search(query, max_results=3)
        overview = self.get_category_overview()

        return f"""
KITOBLAR BAZASI (D:\\1.book — {self.index.get('total_files', 0)} ta fayl):
{overview}

SAVOLGA TEGISHLI MATERIALLAR:
{search_results}
"""

    def get_full_brain_context(self) -> str:
        """Get a comprehensive brain context combining all categories."""
        if not self.index.get("category_summaries"):
            return "BookVault hali indekslanmagan."

        parts = [f"📚 KUTUBXONA BILIMI ({self.index.get('total_files', 0)} ta fayl):\n"]

        for cat, summary in self.index.get("category_summaries", {}).items():
            file_count = len(self.index.get("categories", {}).get(cat, []))
            # Truncate each category summary
            parts.append(f"\n--- {cat} ({file_count} ta fayl) ---\n{summary[:400]}")

        return "\n".join(parts)
