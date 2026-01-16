from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User entity model."""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    password: str = ""
    phone: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'User':
        """Create User from database row (id, name, email, password, phone)."""
        if not row:
            return None
        return cls(
            id=row[0],
            name=row[1] if len(row) > 1 else "",
            email=row[2] if len(row) > 2 else "",
            password=row[3] if len(row) > 3 else "",
            phone=row[4] if len(row) > 4 else None
        )


@dataclass
class Address:
    """Address entity model."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    street: str = ""
    city: str = ""
    zipcode: str = ""

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Address':
        """Create Address from database row."""
        if not row:
            return None
        return cls(
            street=row[0] if len(row) > 0 else "",
            city=row[1] if len(row) > 1 else "",
            zipcode=row[2] if len(row) > 2 else ""
        )
