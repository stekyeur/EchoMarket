import bcrypt
from typing import Tuple, Optional
from repositories.user_repository import UserRepository, AddressRepository


class AuthService:
    """Service for authentication and user management."""

    def __init__(self):
        self.user_repo = UserRepository()
        self.address_repo = AddressRepository()

    def login(self, email: str, password: str) -> Tuple[bool, Optional[dict], str]:
        """
        Authenticate user with email and password.

        Returns:
            Tuple of (success, user_data, message)
            user_data contains 'id' and 'name' if successful
        """
        try:
            user = self.user_repo.find_by_email(email)

            if not user:
                return False, None, "Hatali giris."

            user_id, stored_password, name = user

            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                return True, {'id': user_id, 'name': name}, "Giris basarili!"

            return False, None, "Hatali giris."

        except Exception as e:
            return False, None, "Sunucu hatasi."

    def register(self, full_name: str, email: str, password: str,
                 phone: str = None, street: str = None,
                 city: str = None, zipcode: str = None) -> Tuple[bool, str]:
        """
        Register a new user.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Hash password
            hashed_pw = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            # Create user
            new_user_id = self.user_repo.create(full_name, email, hashed_pw, phone)

            if not new_user_id:
                return False, "Kullanici olusturulamadi."

            # Create address if provided
            if street or city or zipcode:
                self.address_repo.create(new_user_id, street or "", city or "", zipcode or "")

            return True, "Kayit basarili!"

        except Exception as e:
            error_msg = str(e)
            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                return False, "Bu e-posta kayitli."
            return False, error_msg

    def get_user_profile(self, user_id: int) -> Tuple[Optional[tuple], Optional[tuple]]:
        """
        Get user profile with address.

        Returns:
            Tuple of (user_info, address_info)
        """
        user_info = self.user_repo.find_by_id(user_id)
        address_info = self.address_repo.find_by_user_id(user_id)
        return user_info, address_info

    def update_profile(self, user_id: int, name: str, email: str, phone: str,
                       street: str = None, city: str = None, zipcode: str = None,
                       new_password: str = None) -> Tuple[bool, str]:
        """
        Update user profile.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Update user info
            self.user_repo.update(user_id, name, email, phone)

            # Update password if provided
            if new_password:
                hashed = bcrypt.hashpw(
                    new_password.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                self.user_repo.update_password(user_id, hashed)

            # Update or create address
            self.address_repo.upsert(user_id, street or "", city or "", zipcode or "")

            return True, "Bilgiler guncellendi."

        except Exception as e:
            error_msg = str(e)
            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                return False, "E-posta kullanimda."
            return False, error_msg
