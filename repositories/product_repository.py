from typing import List, Optional
from .base import BaseRepository
from models import Product


class ProductRepository(BaseRepository):
    """Repository for Product database operations."""

    BASE_QUERY = """
        SELECT v.id, v.name, v.price, v.image_url, v.category_name,
               COALESCE(AVG(pr.rating), 0) as avg_rating
        FROM view_product_summary v
        LEFT JOIN productrating pr ON v.id = pr.productid
    """
    GROUP_BY = " GROUP BY v.id, v.name, v.price, v.image_url, v.category_name"

    def search_by_name(self, search_term: str, order_by: str = "id",
                       limit: int = 4, offset: int = 0) -> List[tuple]:
        """Search products by name using regex word boundary."""
        pattern = rf"\m{search_term}\M"
        order = self._get_order_clause(order_by)

        query = f"{self.BASE_QUERY} WHERE v.name ~* %s {self.GROUP_BY} {order} LIMIT %s OFFSET %s"
        return self._execute_query(query, (pattern, limit, offset), fetch_all=True) or []

    def search_by_category(self, category: str, order_by: str = "id",
                          limit: int = 4, offset: int = 0) -> List[tuple]:
        """Search products by category name."""
        order = self._get_order_clause(order_by)

        query = f"{self.BASE_QUERY} WHERE v.category_name ILIKE %s {self.GROUP_BY} {order} LIMIT %s OFFSET %s"
        return self._execute_query(query, (f"%{category}%", limit, offset), fetch_all=True) or []

    def get_all(self, order_by: str = "id", limit: int = 4, offset: int = 0) -> List[tuple]:
        """Get all products with optional ordering."""
        order = self._get_order_clause(order_by)

        query = f"{self.BASE_QUERY} {self.GROUP_BY} {order} LIMIT %s OFFSET %s"
        return self._execute_query(query, (limit, offset), fetch_all=True) or []

    def find_by_id(self, product_id: int) -> Optional[tuple]:
        """Find a single product by ID."""
        query = f"{self.BASE_QUERY} WHERE v.id = %s {self.GROUP_BY}"
        return self._execute_query(query, (product_id,), fetch_one=True)

    def _get_order_clause(self, order_by: str) -> str:
        """Get ORDER BY clause based on sort type."""
        order_map = {
            "price_asc": " ORDER BY v.price ASC",
            "price_desc": " ORDER BY v.price DESC",
            "rating": " ORDER BY avg_rating DESC NULLS LAST",
            "id": " ORDER BY v.id"
        }
        return order_map.get(order_by, " ORDER BY v.id")

    def rows_to_products(self, rows: List[tuple]) -> List[Product]:
        """Convert database rows to Product objects."""
        return [Product.from_db_row(row) for row in rows if row]

    def rows_to_dicts(self, rows: List[tuple]) -> List[dict]:
        """Convert database rows to dictionaries."""
        products = self.rows_to_products(rows)
        return [p.to_dict() for p in products]
