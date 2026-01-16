from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Product entity model."""
    id: Optional[int] = None
    name: str = ""
    price: float = 0.0
    image_url: Optional[str] = None
    category_name: Optional[str] = None
    rating: float = 0.0

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Product':
        """Create Product from database row (id, name, price, image_url, category_name, avg_rating)."""
        if not row:
            return None
        return cls(
            id=row[0],
            name=row[1] if len(row) > 1 else "",
            price=float(row[2]) if len(row) > 2 and row[2] else 0.0,
            image_url=row[3] if len(row) > 3 else None,
            category_name=row[4] if len(row) > 4 else None,
            rating=float(round(row[5], 1)) if len(row) > 5 and row[5] else 0.0
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'image': self.image_url or f"https://placehold.co/400?text={self.name}",
            'category': self.category_name,
            'rating': self.rating
        }
