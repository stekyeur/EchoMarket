import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')

    # Database
    DB_CONFIG = {
        "host": os.getenv('DB_HOST'),
        "port": os.getenv('DB_PORT', '5432'),
        "dbname": os.getenv('DB_NAME'),
        "user": os.getenv('DB_USER'),
        "password": os.getenv('DB_PASSWORD')
    }

    # Connection Pool
    DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', 1))
    DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', 20))

    # Voice Recognition Categories
    CATEGORIES = {
        "Kahvaltilik": ["kahvaltilik", "yumurta", "peynir", "zeytin", "recel", "bal", "tereyagi", "kasar", "salam", "sucuk", "sosis", "kremasi", "ekmek", "labne", "yogurt"],
        "Atistirmalik": ["citir cerez", "popcorn", "kuru yemis karisik", "mini kraker", "atistirmalik", "atistirma"],
        "Agiz Bakim": ["dis macunu", "dis fircasi", "agiz gargarasi", "dis ipi", "dis", "agiz", "dil", "agiz bakim"],
        "Banyo Urunleri": ["dus jeli", "sampuan", "sabun", "banyo lifi", "lif", "banyo", "dus", "vucut", "losyon"],
        "Bulasik Makinesi Deterjani": ["bulasik makinesi kapsulu", "toz deterjan", "parlatici", "makine tuzu"],
        "Bulasik Yikama": ["elde bulasik deterjani", "sunger", "bulasik teli", "bulasik deterjani"],
        "Deodorant": ["roll-on", "sprey deodorant", "stick deodorant", "deodorant"],
        "Gazsiz Icecek": ["meyve suyu", "limonata", "soguk cay", "gazsiz icecek", "ice tea", "salep", "kaynak suyu", "toz icecek", "milkshake", "oralet"],
        "Hazir Corba": ["domates corbasi", "mercimek corbasi", "mantar corbasi", "hazir corba", "corba"],
        "Kahvaltilik Gevrek": ["corn flakes", "yulaf ezmesi", "granola", "gevrek", "tahil gevregi"],
        "Kahve": ["turk kahvesi", "filtre kahve", "espresso", "3u1 arada", "latte", "cappuciono", "kahve", "kahvesi"],
        "Kagit Havlu": ["kagit havlu rulo", "cok amacli havlu", "kagit havlu"],
        "Konserveler": ["ton baligi", "misir konservesi", "bezelye konservesi", "konservesi", "konserve"],
        "Kuru Gida": ["pirinc", "bulgur", "mercimek", "nohut", "fasulye", "manti", "baharat", "tarhana", "kurusu", "harci", "sos", "kuru gida"],
        "Kuruyemis": ["findik", "badem", "fistik", "kaju", "karisik kuruyemis", "kuruyemis", "cekirdek", "ceviz", "aycekirdegi"],
        "Makarna": ["spagetti", "burgu makarna", "penne", "fiyonk", "makarna", "eriste", "noodle"],
        "Mutfak Banyo Temizlik": ["camasir suyu", "yuzey temizleyici", "banyo temizleyici", "fayans", "dusakabin", "mutfak temizleyici", "lavabo acici", "yag temizleyici", "kirec", "gider", "firin", "ocak", "sari guc"],
        "Sac Bakimi": ["sampuan", "sac kremi", "sac maskesi", "sac yagi", "dokulme", "sac", "keratin", "tarak"],
        "Sivi Yaglar": ["zeytinyagi", "aycicek yagi", "misir yagi", "sivi yag"],
        "Toz Seker": ["toz sekeri", "pudra sekeri", "esmer seker", "toz seker"],
        "Tiras Urunleri": ["tiras kopugu", "tiras bicagi", "tiras sonrasi losyon", "tiras"],
        "Unlu Mamul": ["pogaca", "simit", "borek", "corek", "kombe", "kurabiye", "katmer"],
        "Camasir Deterjani": ["toz deterjan", "sivi deterjan", "kapsul deterjan"],
        "Camasir Yikama Urunleri": ["leke cikarici", "renk koruyucu", "camasir filesi", "deterjan"],
        "Cikolata": ["cikolata"],
        "Cay": ["cay"],
        "Sut": ["sut"],
        "Kek": ["kek"],
        "Protein Bar": ["protein bar"],
        "Salca": ["salca"],
        "Tuvalet Kagidi": ["tuvalet kagidi"],
        "Yumusatici": ["yumusatici"],
        "Un": ["un"],
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()
