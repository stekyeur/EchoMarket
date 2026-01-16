from .base import BaseRepository
from models import User, Address


class UserRepository(BaseRepository):
    """Repository for User database operations."""

    def find_by_email(self, email: str) -> tuple:
        """Find user by email. Returns (id, password, name) tuple."""
        query = 'SELECT id, password, name FROM "user" WHERE email = %s'
        return self._execute_query(query, (email,), fetch_one=True)

    def find_by_id(self, user_id: int) -> tuple:
        """Find user by ID. Returns (name, email, phone) tuple."""
        query = 'SELECT name, email, phone FROM "user" WHERE id = %s'
        return self._execute_query(query, (user_id,), fetch_one=True)

    def create(self, name: str, email: str, hashed_password: str, phone: str = None) -> int:
        """Create a new user. Returns the new user ID."""
        query = 'INSERT INTO "user" (name, email, password, phone) VALUES (%s, %s, %s, %s) RETURNING id'
        result = self._execute_write(query, (name, email, hashed_password, phone), returning=True)
        return result[0] if result else None

    def update(self, user_id: int, name: str, email: str, phone: str) -> bool:
        """Update user information."""
        query = 'UPDATE "user" SET name=%s, phone=%s, email=%s WHERE id=%s'
        self._execute_write(query, (name, phone, email, user_id))
        return True

    def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update user password."""
        query = 'UPDATE "user" SET password=%s WHERE id=%s'
        self._execute_write(query, (hashed_password, user_id))
        return True


class AddressRepository(BaseRepository):
    """Repository for Address database operations."""

    def find_by_user_id(self, user_id: int) -> tuple:
        """Find address by user ID. Returns (street, city, zipcode) tuple."""
        query = 'SELECT street, city, zipcode FROM address WHERE userid = %s'
        return self._execute_query(query, (user_id,), fetch_one=True)

    def exists(self, user_id: int) -> bool:
        """Check if user has an address."""
        query = 'SELECT id FROM address WHERE userid = %s'
        result = self._execute_query(query, (user_id,), fetch_one=True)
        return result is not None

    def create(self, user_id: int, street: str, city: str, zipcode: str) -> bool:
        """Create a new address for user."""
        query = 'INSERT INTO address (userid, street, city, zipcode) VALUES (%s, %s, %s, %s)'
        self._execute_write(query, (user_id, street, city, zipcode))
        return True

    def update(self, user_id: int, street: str, city: str, zipcode: str) -> bool:
        """Update user address."""
        query = 'UPDATE address SET street=%s, city=%s, zipcode=%s WHERE userid=%s'
        self._execute_write(query, (street, city, zipcode, user_id))
        return True

    def upsert(self, user_id: int, street: str, city: str, zipcode: str) -> bool:
        """Create or update address."""
        if self.exists(user_id):
            return self.update(user_id, street, city, zipcode)
        return self.create(user_id, street, city, zipcode)
