from typing import List, Tuple, Optional
from repositories.product_repository import ProductRepository
from models import Product


class ProductService:
    """Service for product search and listing."""

    def __init__(self):
        self.product_repo = ProductRepository()

    def search_products(self, query: str, page: int = 1,
                       is_cheapest: bool = False, is_expensive: bool = False,
                       is_top_rated: bool = False) -> Tuple[List[dict], str]:
        """
        Search products with filters.

        Returns:
            Tuple of (products_list, message)
        """
        clean_query = self._clean_search_text(query)
        order_by = self._get_order_by(is_cheapest, is_expensive, is_top_rated)
        offset = (page - 1) * 4

        rows = []
        found_title = None

        # 1. Search by name
        if clean_query:
            rows = self.product_repo.search_by_name(clean_query, order_by, limit=4, offset=offset)
            if rows:
                found_title = f"'{clean_query}' aramasi"

        # 2. Search by category
        if not rows and clean_query:
            rows = self.product_repo.search_by_category(clean_query, order_by, limit=4, offset=offset)
            if rows:
                found_title = f"'{clean_query}' kategorisi"

        # 3. Filter only (no search term)
        if not rows and not clean_query and (is_cheapest or is_expensive or is_top_rated):
            rows = self.product_repo.get_all(order_by, limit=4, offset=offset)
            if is_expensive:
                found_title = "En yuksek fiyatli urunler"
            elif is_cheapest:
                found_title = "En uygun fiyatli urunler"
            elif is_top_rated:
                found_title = "En yuksek puanli urunler"

        products = self.product_repo.rows_to_dicts(rows)
        message = f"{found_title} bulundu." if found_title else "Sonuclar bulundu."

        return products, message

    def get_products_for_market(self, query: str = "", page: int = 1) -> List[dict]:
        """Get products for market page with pagination."""
        is_cheapest = "en ucuz" in query or "uygun" in query or "en dusuk fiyat" in query
        is_expensive = "en pahali" in query or "en yuksek fiyat" in query
        is_top_rated = "en iyi" in query or "yuksek puan" in query

        products, _ = self.search_products(query, page, is_cheapest, is_expensive, is_top_rated)
        return products

    def detect_filters(self, query: str) -> Tuple[bool, bool, bool]:
        """Detect filter flags from query string."""
        query_lower = query.lower()
        is_cheapest = "en ucuz" in query_lower or "uygun" in query_lower or "en dusuk fiyat" in query_lower
        is_expensive = "en pahali" in query_lower or "en yuksek fiyat" in query_lower
        is_top_rated = "en iyi" in query_lower or "yuksek puan" in query_lower
        return is_cheapest, is_expensive, is_top_rated

    def _get_order_by(self, is_cheapest: bool, is_expensive: bool, is_top_rated: bool) -> str:
        """Get order_by value based on filter flags."""
        if is_cheapest:
            return "price_asc"
        if is_expensive:
            return "price_desc"
        if is_top_rated:
            return "rating"
        return "id"

    def _clean_search_text(self, text: str) -> str:
        """Clean search text by removing filler words."""
        if not text:
            return ""

        text = text.lower()

        # Filler phrases to remove
        filler_phrases = [
            "satin almak istiyorum", "almak istiyorum", "istiyorum",
            "ariyorum", "bul", "getir", "goster", "listele",
            "bana", "satin al", "alacagim", "lazim", "var mi",
            "bulsana", "ekle", "siparis ver", "bak", "bakar misin"
        ]
        for phrase in filler_phrases:
            text = text.replace(phrase, "")

        # Filter words to remove
        filter_words = [
            "en ucuz", "uygun fiyatli", "uygun", "en dusuk fiyatli",
            "en pahali", "en yuksek fiyatli", "pahali",
            "en iyi", "en yuksek puan", "yuksek puan", "en yuksek puanli",
            "onerilen", "kaliteli"
        ]
        for f in filter_words:
            text = text.replace(f, "")

        return " ".join(text.split())
