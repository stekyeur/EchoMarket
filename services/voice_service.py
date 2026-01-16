import speech_recognition as sr
from typing import Tuple, Optional
from flask import session
from config.settings import get_config

config = get_config()


class VoiceService:
    """Service for voice command processing."""

    # Voice states stored in session
    STATE_KEY = 'voice_state'
    CATEGORY_KEY = 'voice_last_category'

    # State constants
    STATE_MAIN_MENU = "MAIN_MENU"
    STATE_SEARCH = "SEARCH"
    STATE_CATEGORY_CONFIRM = "CATEGORY_CONFIRM"
    STATE_LIST_PRODUCTS = "LIST_PRODUCTS"

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.categories = config.CATEGORIES

    def get_state(self) -> str:
        """Get current voice state from session."""
        return session.get(self.STATE_KEY, self.STATE_MAIN_MENU)

    def set_state(self, state: str):
        """Set voice state in session."""
        session[self.STATE_KEY] = state

    def get_last_category(self) -> Optional[str]:
        """Get last detected category from session."""
        return session.get(self.CATEGORY_KEY)

    def set_last_category(self, category: str):
        """Set last category in session."""
        session[self.CATEGORY_KEY] = category

    def listen(self) -> Tuple[bool, str, str]:
        """
        Listen for voice command.

        Returns:
            Tuple of (success, command, error_message)
        """
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.recognizer.energy_threshold = 400
                self.recognizer.dynamic_energy_threshold = False
                self.recognizer.pause_threshold = 0.8

                print("Dinliyorum...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                command = self.recognizer.recognize_google(audio, language='tr-tr').lower()

                return True, command, ""

        except sr.WaitTimeoutError:
            return False, "", "Sure doldu, ses gelmedi."
        except sr.UnknownValueError:
            return False, "", "Anlasilamadi."
        except Exception as e:
            print(f"Voice Error: {e}")
            return False, "", "Sistem hatasi."

    def process_command(self, command: str) -> dict:
        """
        Process voice command and return response.

        Returns:
            Response dict with keys: status, command, message, state, action, redirect_url, query, category
        """
        current_state = self.get_state()

        response = {
            'status': 'success',
            'command': command,
            'message': f"Algilanan: {command}",
            'state': current_state
        }

        # 1. Page navigation commands
        if any(word in command for word in ["sonraki", "diger", "hicbiri", "devam"]):
            response.update({
                "action": "next_page",
                "message": "Diger urunler getiriliyor."
            })
            return response

        # 2. Global redirects
        if "cikis" in command or "oturumu kapat" in command:
            response.update({
                "action": "redirect",
                "redirect_url": "/logout",
                "message": "Cikis yapiliyor."
            })
            return response

        if "giris" in command:
            response.update({
                "action": "redirect",
                "redirect_url": "/login",
                "message": "Giris ekranina yonlendiriliyorsunuz."
            })
            return response

        if "kayit" in command:
            response.update({
                "action": "redirect",
                "redirect_url": "/register",
                "message": "Kayit ekranina yonlendiriliyorsunuz."
            })
            return response

        # 3. State-based commands
        if current_state == self.STATE_MAIN_MENU:
            return self._handle_main_menu(command, response)
        elif current_state == self.STATE_SEARCH:
            return self._handle_search(command, response)
        elif current_state == self.STATE_CATEGORY_CONFIRM:
            return self._handle_category_confirm(command, response)

        return response

    def _handle_main_menu(self, command: str, response: dict) -> dict:
        """Handle commands in main menu state."""
        if "sepet" in command:
            response.update({
                "state": "OPEN_CART",
                "action": "redirect",
                "redirect_url": "/cart"
            })
        elif "hesabim" in command:
            response.update({
                "state": "ACCOUNT",
                "action": "redirect",
                "redirect_url": "/account"
            })
        elif "market" in command:
            response.update({
                "state": "MARKET",
                "action": "redirect",
                "redirect_url": "/market"
            })
        elif "urun" in command or "al" in command:
            self.set_state(self.STATE_SEARCH)
            response.update({
                "state": self.STATE_SEARCH,
                "message": "Ne almak istersiniz?"
            })

        return response

    def _handle_search(self, command: str, response: dict) -> dict:
        """Handle commands in search state."""
        # Try to find category
        category = self._find_category(command)

        if category:
            self.set_last_category(category)
            self.set_state(self.STATE_CATEGORY_CONFIRM)
            response.update({
                "state": self.STATE_CATEGORY_CONFIRM,
                "category": category,
                "message": f"{category} bulundu, listeleyeyim mi?"
            })
        else:
            response.update({
                "state": self.STATE_SEARCH,
                "message": "Kategori anlasilamadi, urun araniyor..."
            })

        return response

    def _handle_category_confirm(self, command: str, response: dict) -> dict:
        """Handle commands in category confirm state."""
        if "evet" in command or "listele" in command:
            self.set_state(self.STATE_LIST_PRODUCTS)
            response.update({
                "state": self.STATE_LIST_PRODUCTS,
                "query": self.get_last_category()
            })
        else:
            self.set_state(self.STATE_MAIN_MENU)
            response.update({
                "state": self.STATE_MAIN_MENU,
                "message": "Iptal edildi."
            })

        return response

    def _find_category(self, command: str) -> Optional[str]:
        """Find category from command."""
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in command:
                    return category
        return None

    def reset_state(self):
        """Reset voice state to main menu."""
        self.set_state(self.STATE_MAIN_MENU)
        session.pop(self.CATEGORY_KEY, None)
