from typing import Tuple, Optional, List
from repositories.order_repository import OrderRepository
from repositories.cart_repository import CartRepository
from services.cart_service import CartService


class OrderService:
    """Service for order operations."""

    def __init__(self):
        self.order_repo = OrderRepository()
        self.cart_repo = CartRepository()
        self.cart_service = CartService()

    def create_order(self, user_id: int) -> Tuple[bool, Optional[int], str]:
        """
        Create order from user's cart.

        Returns:
            Tuple of (success, order_id, message)
        """
        try:
            # Get checkout data
            session_id, items, total = self.cart_service.get_checkout_data(user_id)

            if not session_id or not items:
                return False, None, "Sepet bos."

            # Create order
            order_id = self.order_repo.create_order(user_id, total)

            if not order_id:
                return False, None, "Siparis olusturulamadi."

            # Create order items
            for product_id, quantity, price in items:
                self.order_repo.create_order_item(order_id, product_id, quantity, price)

            # Clear cart
            self.cart_repo.clear_cart(session_id)

            return True, order_id, "Siparis olusturuldu."

        except Exception as e:
            return False, None, str(e)

    def get_order_details(self, order_id: int, user_id: int) -> Tuple[Optional[tuple], List[tuple]]:
        """
        Get order details with items.

        Returns:
            Tuple of (order_info, order_items)
            order_info: (id, totalamount, orderdate, status)
            order_items: [(name, quantity, price, image_url), ...]
        """
        order = self.order_repo.get_order(order_id, user_id)
        if not order:
            return None, []

        items = self.order_repo.get_order_items(order_id)
        return order, items

    def get_user_orders(self, user_id: int) -> List[tuple]:
        """Get all orders for a user."""
        return self.order_repo.get_user_orders(user_id)
