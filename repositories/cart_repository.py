from typing import List, Optional
from .base import BaseRepository


class CartRepository(BaseRepository):
    """Repository for Cart/Shopping Session database operations."""

    def get_session_id(self, user_id: int) -> Optional[int]:
        """Get shopping session ID for user."""
        query = 'SELECT id FROM shoppingsession WHERE userid = %s'
        result = self._execute_query(query, (user_id,), fetch_one=True)
        return result[0] if result else None

    def create_session(self, user_id: int) -> int:
        """Create a new shopping session for user. Returns session ID."""
        query = 'INSERT INTO shoppingsession (userid) VALUES (%s) RETURNING id'
        result = self._execute_write(query, (user_id,), returning=True)
        return result[0] if result else None

    def get_or_create_session(self, user_id: int) -> int:
        """Get existing session or create new one."""
        session_id = self.get_session_id(user_id)
        if session_id is None:
            session_id = self.create_session(user_id)
        return session_id

    def get_cart_items(self, session_id: int) -> List[tuple]:
        """Get all items in cart. Returns (name, price, quantity, subtotal, image_url, product_id)."""
        query = """
            SELECT p.name, p.price, ci.quantity, (p.price * ci.quantity), p.image_url, p.id
            FROM cartitem ci
            JOIN product p ON ci.productid = p.id
            WHERE ci.sessionid = %s
            ORDER BY p.name
        """
        return self._execute_query(query, (session_id,), fetch_all=True) or []

    def get_cart_count(self, user_id: int) -> int:
        """Get total quantity of items in user's cart."""
        session_id = self.get_session_id(user_id)
        if not session_id:
            return 0

        query = 'SELECT SUM(quantity) FROM cartitem WHERE sessionid = %s'
        result = self._execute_query(query, (session_id,), fetch_one=True)
        return int(result[0]) if result and result[0] else 0

    def get_item(self, session_id: int, product_id: int) -> Optional[tuple]:
        """Get a specific cart item. Returns (id, quantity)."""
        query = 'SELECT id, quantity FROM cartitem WHERE sessionid=%s AND productid=%s'
        return self._execute_query(query, (session_id, product_id), fetch_one=True)

    def add_item(self, session_id: int, product_id: int, quantity: int = 1) -> bool:
        """Add a new item to cart."""
        query = 'INSERT INTO cartitem (sessionid, productid, quantity) VALUES (%s, %s, %s)'
        self._execute_write(query, (session_id, product_id, quantity))
        return True

    def update_item_quantity(self, item_id: int, quantity: int) -> bool:
        """Update cart item quantity by item ID."""
        query = 'UPDATE cartitem SET quantity=%s WHERE id=%s'
        self._execute_write(query, (quantity, item_id))
        return True

    def update_quantity_by_product(self, session_id: int, product_id: int, quantity: int) -> bool:
        """Update cart item quantity by session and product ID."""
        query = 'UPDATE cartitem SET quantity=%s WHERE sessionid=%s AND productid=%s'
        self._execute_write(query, (quantity, session_id, product_id))
        return True

    def remove_item(self, session_id: int, product_id: int) -> bool:
        """Remove an item from cart."""
        query = 'DELETE FROM cartitem WHERE sessionid=%s AND productid=%s'
        self._execute_write(query, (session_id, product_id))
        return True

    def clear_cart(self, session_id: int) -> bool:
        """Remove all items from cart."""
        query = 'DELETE FROM cartitem WHERE sessionid=%s'
        self._execute_write(query, (session_id,))
        return True

    def get_items_for_checkout(self, session_id: int) -> List[tuple]:
        """Get cart items with price info for checkout. Returns (product_id, quantity, price)."""
        query = """
            SELECT ci.productid, ci.quantity, p.price
            FROM cartitem ci
            JOIN product p ON ci.productid = p.id
            WHERE ci.sessionid = %s
        """
        return self._execute_query(query, (session_id,), fetch_all=True) or []
