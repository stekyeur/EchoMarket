from dataclasses import dataclass
from typing import Optional


@dataclass
class ShoppingSession:
    """Shopping session entity model."""
    id: Optional[int] = None
    user_id: Optional[int] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ShoppingSession':
        """Create ShoppingSession from database row."""
        if not row:
            return None
        return cls(id=row[0])


@dataclass
class CartItem:
    """Cart item entity model."""
    id: Optional[int] = None
    session_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: int = 0
    # Joined fields from product
    product_name: str = ""
    product_price: float = 0.0
    product_image: Optional[str] = None
    subtotal: float = 0.0

    @classmethod
    def from_db_row(cls, row: tuple) -> 'CartItem':
        """Create CartItem from database row (name, price, quantity, subtotal, image_url, product_id)."""
        if not row:
            return None
        return cls(
            product_name=row[0] if len(row) > 0 else "",
            product_price=float(row[1]) if len(row) > 1 and row[1] else 0.0,
            quantity=int(row[2]) if len(row) > 2 and row[2] else 0,
            subtotal=float(row[3]) if len(row) > 3 and row[3] else 0.0,
            product_image=row[4] if len(row) > 4 else None,
            product_id=row[5] if len(row) > 5 else None
        )

    def to_tuple(self) -> tuple:
        """Convert to tuple for template compatibility."""
        return (
            self.product_name,
            self.product_price,
            self.quantity,
            self.subtotal,
            self.product_image,
            self.product_id
        )
