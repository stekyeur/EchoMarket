from typing import List, Tuple, Optional
from repositories.cart_repository import CartRepository


class CartService:
    """Service for shopping cart operations."""

    def __init__(self):
        self.cart_repo = CartRepository()

    def get_cart_count(self, user_id: int) -> int:
        """Get total item count in user's cart."""
        try:
            return self.cart_repo.get_cart_count(user_id)
        except:
            return 0

    def get_cart_items(self, user_id: int) -> Tuple[List[tuple], float]:
        """
        Get all cart items for user.

        Returns:
            Tuple of (cart_items, total_amount)
        """
        session_id = self.cart_repo.get_session_id(user_id)
        if not session_id:
            return [], 0.0

        items = self.cart_repo.get_cart_items(session_id)
        total = sum(item[3] for item in items) if items else 0.0

        return items, total

    def add_to_cart(self, user_id: int, product_id: int) -> Tuple[bool, int, str]:
        """
        Add product to cart.

        Returns:
            Tuple of (success, cart_count, message)
        """
        try:
            # Get or create session
            session_id = self.cart_repo.get_or_create_session(user_id)

            # Check if item exists
            existing_item = self.cart_repo.get_item(session_id, product_id)

            if existing_item:
                # Increase quantity
                item_id, quantity = existing_item
                self.cart_repo.update_item_quantity(item_id, quantity + 1)
            else:
                # Add new item
                self.cart_repo.add_item(session_id, product_id, 1)

            cart_count = self.cart_repo.get_cart_count(user_id)
            return True, cart_count, "Urun sepete eklendi."

        except Exception as e:
            return False, 0, str(e)

    def update_cart_item(self, user_id: int, product_id: int, action: str) -> Tuple[bool, int, str]:
        """
        Update cart item quantity (increase/decrease).

        Returns:
            Tuple of (success, cart_count, message)
        """
        try:
            session_id = self.cart_repo.get_session_id(user_id)
            if not session_id:
                return False, 0, "Sepet bulunamadi."

            item = self.cart_repo.get_item(session_id, product_id)
            if not item:
                return False, 0, "Urun bulunamadi."

            _, current_qty = item
            new_qty = current_qty + 1 if action == 'increase' else current_qty - 1

            if new_qty > 0:
                self.cart_repo.update_quantity_by_product(session_id, product_id, new_qty)
            else:
                self.cart_repo.remove_item(session_id, product_id)

            cart_count = self.cart_repo.get_cart_count(user_id)
            return True, cart_count, "Sepet guncellendi."

        except Exception as e:
            return False, 0, str(e)

    def remove_item(self, user_id: int, product_id: int) -> Tuple[bool, str]:
        """
        Remove item from cart.

        Returns:
            Tuple of (success, message)
        """
        try:
            session_id = self.cart_repo.get_session_id(user_id)
            if not session_id:
                return False, "Sepet bulunamadi."

            self.cart_repo.remove_item(session_id, product_id)
            return True, "Urun kaldirildi."

        except Exception as e:
            return False, str(e)

    def clear_cart(self, user_id: int) -> Tuple[bool, str]:
        """
        Clear all items from cart.

        Returns:
            Tuple of (success, message)
        """
        try:
            session_id = self.cart_repo.get_session_id(user_id)
            if session_id:
                self.cart_repo.clear_cart(session_id)
            return True, "Sepet temizlendi."

        except Exception as e:
            return False, str(e)

    def get_checkout_data(self, user_id: int) -> Tuple[Optional[int], List[tuple], float]:
        """
        Get cart data for checkout.

        Returns:
            Tuple of (session_id, items, total)
            items: [(product_id, quantity, price), ...]
        """
        session_id = self.cart_repo.get_session_id(user_id)
        if not session_id:
            return None, [], 0.0

        items = self.cart_repo.get_items_for_checkout(session_id)
        total = sum(item[1] * item[2] for item in items)

        return session_id, items, total
