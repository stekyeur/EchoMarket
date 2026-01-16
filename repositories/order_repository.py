from typing import List, Optional
from datetime import date
from .base import BaseRepository


class OrderRepository(BaseRepository):
    """Repository for Order database operations."""

    def create_order(self, user_id: int, total_amount: float, status: str = "Hazirlaniyor") -> int:
        """Create a new order. Returns order ID."""
        query = '''
            INSERT INTO "Order" (userid, orderdate, totalamount, status)
            VALUES (%s, %s, %s, %s) RETURNING id
        '''
        result = self._execute_write(
            query,
            (user_id, date.today(), total_amount, status),
            returning=True
        )
        return result[0] if result else None

    def create_order_item(self, order_id: int, product_id: int, quantity: int, price: float) -> bool:
        """Create an order item."""
        query = 'INSERT INTO orderitem (orderid, productid, quantity, price) VALUES (%s, %s, %s, %s)'
        self._execute_write(query, (order_id, product_id, quantity, price))
        return True

    def get_user_orders(self, user_id: int) -> List[tuple]:
        """Get all orders for a user. Returns (id, totalamount, orderdate, status)."""
        query = '''
            SELECT id, totalamount, orderdate, status
            FROM "Order"
            WHERE userid = %s
            ORDER BY orderdate DESC
        '''
        return self._execute_query(query, (user_id,), fetch_all=True) or []

    def get_order(self, order_id: int, user_id: int) -> Optional[tuple]:
        """Get a specific order. Returns (id, totalamount, orderdate, status)."""
        query = '''
            SELECT id, totalamount, orderdate, status
            FROM "Order"
            WHERE id = %s AND userid = %s
        '''
        return self._execute_query(query, (order_id, user_id), fetch_one=True)

    def get_order_items(self, order_id: int) -> List[tuple]:
        """Get order items. Returns (name, quantity, price, image_url)."""
        query = '''
            SELECT p.name, oi.quantity, oi.price, p.image_url
            FROM orderitem oi
            JOIN product p ON oi.productid = p.id
            WHERE oi.orderid = %s
        '''
        return self._execute_query(query, (order_id,), fetch_all=True) or []

    def update_status(self, order_id: int, status: str) -> bool:
        """Update order status."""
        query = 'UPDATE "Order" SET status = %s WHERE id = %s'
        self._execute_write(query, (status, order_id))
        return True
