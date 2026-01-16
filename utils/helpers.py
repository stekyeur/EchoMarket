def clean_search_text(text: str) -> str:
    """
    Clean search text by removing filler words and filter phrases.

    Args:
        text: Raw search query

    Returns:
        Cleaned search query
    """
    if not text:
        return ""

    text = text.lower()

    # Filler phrases to remove (Turkish)
    filler_phrases = [
        "satin almak istiyorum", "almak istiyorum", "istiyorum",
        "ariyorum", "bul", "getir", "goster", "listele",
        "bana", "satin al", "alacagim", "lazim", "var mi",
        "bulsana", "ekle", "siparis ver", "bak", "bakar misin"
    ]
    for phrase in filler_phrases:
        text = text.replace(phrase, "")

    # Filter words to remove
    filter_words = [
        "en ucuz", "uygun fiyatli", "uygun", "en dusuk fiyatli",
        "en pahali", "en yuksek fiyatli", "pahali",
        "en iyi", "en yuksek puan", "yuksek puan", "en yuksek puanli",
        "onerilen", "kaliteli"
    ]
    for f in filter_words:
        text = text.replace(f, "")

    return " ".join(text.split())


def format_price(price: float) -> str:
    """Format price for display."""
    return f"{price:.2f} TL"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
