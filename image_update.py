import psycopg2
from config import DB_CONFIG

# --- 1. ERİŞİLEBİLİR GÖRSEL KÜTÜPHANESİ (YATAY & NET) ---
IMG_CIPS      = "https://images.unsplash.com/photo-1585238342028-4bbc3d83f0a4?w=900&fit=crop"
IMG_DIS       = "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=900&fit=crop"
IMG_SABUN     = "https://images.unsplash.com/photo-1588774069410-84ae30757c7a?w=900&fit=crop"
IMG_BULASIK   = "https://images.unsplash.com/photo-1581579185169-dde0c75b44a1?w=900&fit=crop"
IMG_DEODORANT = "https://images.unsplash.com/photo-1619451334792-150fd785ee74?w=900&fit=crop"
IMG_ICECEK    = "https://images.unsplash.com/photo-1543253687-c5965043d534?w=900&fit=crop"
IMG_CORBA     = "https://images.unsplash.com/photo-1547592166-23acbe3a624b?w=900&fit=crop"
IMG_GEVREK    = "https://images.unsplash.com/photo-1521483451569-e33803c033bf?w=900&fit=crop"
IMG_KAHVALTI  = "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=900&fit=crop"
IMG_KAHVE     = "https://images.unsplash.com/photo-1559496417-e7f25cb247f3?w=900&fit=crop"
IMG_KAGIT     = "https://images.unsplash.com/photo-1583947581924-860bda6a26df?w=900&fit=crop"
IMG_KEK       = "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=900&fit=crop"
IMG_KONSERVE  = "https://images.unsplash.com/photo-1584269631720-7f2873428988?w=900&fit=crop"
IMG_KURU_GIDA = "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=900&fit=crop"
IMG_CEREZ     = "https://images.unsplash.com/photo-1603569283847-aa295f0d016a?w=900&fit=crop"
IMG_MAKARNA   = "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=900&fit=crop"
IMG_TEMIZLIK  = "https://images.unsplash.com/photo-1585837575652-2c69d0a6df39?w=900&fit=crop"
IMG_BAR       = "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=900&fit=crop"
IMG_SALCA     = "https://images.unsplash.com/photo-1596524430615-b46476ddff6e?w=900&fit=crop"
IMG_SAMPUAN   = "https://images.unsplash.com/photo-1585232561025-aa8731057e4e?w=900&fit=crop"
IMG_SUT       = "https://images.unsplash.com/photo-1559598467-f8b76c8155d0?w=900&fit=crop"
IMG_YAG       = "https://images.unsplash.com/photo-1474979266404-7cadd259c308?w=900&fit=crop"
IMG_SEKER     = "https://images.unsplash.com/photo-1581441363689-1f3c3c414635?w=900&fit=crop"
IMG_TRAŞ      = "https://images.unsplash.com/photo-1621607512214-68297480165e?w=900&fit=crop"
IMG_UN        = "https://images.unsplash.com/photo-1627485937980-221c88ac04f9?w=900&fit=crop"
IMG_CAMASIR   = "https://images.unsplash.com/photo-1626806819282-2c1dc01a5e0c?w=900&fit=crop"
IMG_CAY       = "https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?w=900&fit=crop"
IMG_CIKOLATA  = "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=900&fit=crop"

def fix_images_exact_categories():
    conn = None
    try:
        print("Veritabanına bağlanılıyor...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        category_map = {
            "Atıştırmalık": IMG_CIPS,
            "Cips": IMG_CIPS,
            "Kraker": IMG_CIPS,
            "Ağız Bakım": IMG_DIS,
            "Banyo Ürünleri": IMG_SABUN,
            "Bulaşık Makinesi Deterjanı": IMG_BULASIK,
            "Bulaşık Yıkama": IMG_BULASIK,
            "Deodorant": IMG_DEODORANT,
            "Gazsız İçecek": IMG_ICECEK,
            "Hazır Çorba": IMG_CORBA,
            "Kahvaltılık Gevrek": IMG_GEVREK,
            "Kahvaltılık": IMG_KAHVALTI,
            "Kahve": IMG_KAHVE,
            "Kağıt Havlu": IMG_KAGIT,
            "Tuvalet Kağıdı": IMG_KAGIT,
            "Kek": IMG_KEK,
            "Unlu Mamül": IMG_KEK,
            "Konserveler": IMG_KONSERVE,
            "Kuru Gıda": IMG_KURU_GIDA,
            "Kuruyemiş": IMG_CEREZ,
            "Makarna": IMG_MAKARNA,
            "Mutfak Banyo Temizlik": IMG_TEMIZLIK,
            "Protein Bar": IMG_BAR,
            "Salça": IMG_SALCA,
            "Saç Bakımı": IMG_SAMPUAN,
            "Süt": IMG_SUT,
            "Sıvı Yağlar": IMG_YAG,
            "Toz Şeker": IMG_SEKER,
            "Tıraş Ürünleri": IMG_TRAŞ,
            "Un": IMG_UN,
            "Yumuşatıcılar": IMG_CAMASIR,
            "Çamaşır Deterjanı": IMG_CAMASIR,
            "Çamaşır Yıkama Ürünleri": IMG_CAMASIR,
            "Çay": IMG_CAY,
            "Çikolata": IMG_CIKOLATA
        }

        print("Kategorilere göre kesin güncelleme başlıyor...")
        print("-" * 40)

        total_updated = 0

        for cat_name, img_url in category_map.items():
            sql = """
                UPDATE product
                SET image_url = %s
                FROM category
                WHERE product.categoryid = category.id
                AND category.name = %s
            """
            cur.execute(sql, (img_url, cat_name))

            if cur.rowcount > 0:
                print(f"✅ '{cat_name}' -> {cur.rowcount} ürün güncellendi.")
                total_updated += cur.rowcount
            else:
                print(f"⚠️ '{cat_name}' için eşleşme yok.")

        conn.commit()
        print("-" * 40)
        print(f"🎉 TOPLAM {total_updated} ÜRÜN GÜNCELLENDİ.")

    except Exception as e:
        print(f"❌ Hata: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_images_exact_categories()
