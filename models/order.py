from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class Order:
    """Order entity model."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    order_date: Optional[date] = None
    total_amount: float = 0.0
    status: str = "Hazirlaniyor"

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Order':
        """Create Order from database row (id, totalamount, orderdate, status)."""
        if not row:
            return None
        return cls(
            id=row[0],
            total_amount=float(row[1]) if len(row) > 1 and row[1] else 0.0,
            order_date=row[2] if len(row) > 2 else None,
            status=row[3] if len(row) > 3 else "Hazirlaniyor"
        )

    def to_tuple(self) -> tuple:
        """Convert to tuple for template compatibility."""
        return (self.id, self.total_amount, self.order_date, self.status)


@dataclass
class OrderItem:
    """Order item entity model."""
    id: Optional[int] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: int = 0
    price: float = 0.0
    # Joined fields
    product_name: str = ""
    product_image: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'OrderItem':
        """Create OrderItem from database row (name, quantity, price, image_url)."""
        if not row:
            return None
        return cls(
            product_name=row[0] if len(row) > 0 else "",
            quantity=int(row[1]) if len(row) > 1 and row[1] else 0,
            price=float(row[2]) if len(row) > 2 and row[2] else 0.0,
            product_image=row[3] if len(row) > 3 else None
        )

    def to_tuple(self) -> tuple:
        """Convert to tuple for template compatibility."""
        return (self.product_name, self.quantity, self.price, self.product_image)
