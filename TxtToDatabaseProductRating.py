import os
import pandas as pd
import psycopg2
from psycopg2 import extras # Hız için gerekli ek paket
import random

# --- AYARLAR ---
DOSYA_KLASORU = r"C:\Users\arzuf\OneDrive\Belgeler\GitHub\EchoMarket\txtler"

# --- BAĞLANTI BİLGİLERİ (Hızlı Port) ---
DB_CONFIG = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": "5432",
    "dbname": "postgres",
    "user": "postgres.zhulbmvyuszoiutbthpu", 
    "password": "jGF6nkMVNK9rAxYk", 
    "sslmode": "prefer"
}

# --- YARDIMCI FONKSİYONLAR ---
def clean_rating(rating_str):
    if pd.isna(rating_str): return None
    try:
        return float(str(rating_str).replace(',', '.'))
    except:
        return None

def clean_reviews(review_str):
    if pd.isna(review_str): return 0
    try:
        clean = str(review_str).replace('(', '').replace(')', '').replace('.', '')
        return int(clean)
    except:
        return 0

def generate_weighted_rating(target_rating):
    if not target_rating: return 5
    base = int(target_rating)
    probability = target_rating - base
    return base + 1 if random.random() < probability else base

def main():
    print("\n--- PRODUCT RATING OLUŞTURUCU (TURBO MOD 🚀) ---")
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Veritabanına bağlanıldı.")
        
        # 1. Verileri Hafızaya Al
        print("📥 Kullanıcı ve Ürün listeleri alınıyor...")
        cursor.execute('SELECT id FROM "user"')
        all_user_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('SELECT name, id FROM product')
        product_map = {row[0]: row[1] for row in cursor.fetchall()}
        
        print(f"   -> {len(all_user_ids)} kullanıcı, {len(product_map)} ürün bulundu.")
        
        if not all_user_ids:
            print("❌ HATA: Kullanıcı yok!")
            return

        if not os.path.exists(DOSYA_KLASORU):
            print("❌ Klasör bulunamadı.")
            return

        print("\n🚀 İşlem Başlıyor (Paketler halinde gönderilecek)...")
        total_ratings_inserted = 0
        
        # SQL Şablonu (Hız için execute_values kullanacağız)
        insert_query = """
            INSERT INTO productrating (userid, productid, rating, ratedate)
            VALUES %s
            ON CONFLICT (userid, productid) DO NOTHING
        """

        for dosya_adi in os.listdir(DOSYA_KLASORU):
            if dosya_adi.endswith(".txt"):
                print(f"📄 Hazırlanıyor: {dosya_adi}", end=" ")
                dosya_yolu = os.path.join(DOSYA_KLASORU, dosya_adi)
                
                # Bu dosya için birikecek oylar listesi
                batch_data = []
                
                try:
                    df = pd.read_csv(dosya_yolu, on_bad_lines='skip')
                    
                    for _, row in df.iterrows():
                        urun_adi = str(row['Name'])
                        if urun_adi not in product_map: continue 
                            
                        product_id = product_map[urun_adi]
                        target = clean_rating(row.get('Rating'))
                        count = clean_reviews(row.get('Reviews'))
                        
                        if not target or count == 0: continue

                        limit = min(count, len(all_user_ids))
                        selected_users = random.sample(all_user_ids, limit)
                        
                        for user_id in selected_users:
                            score = generate_weighted_rating(target)
                            # Listeye ekle (Veritabanına hemen gitme!)
                            # (userid, productid, rating, ratedate) formatında
                            # ratedate için veritabanında default NOW() var ama execute_values için
                            # Python tarafında 'now' yerine doğrudan SQL keyword'ü zor olduğu için
                            # ya datetime.now() vereceğiz ya da SQL'i düzelteceğiz.
                            # Basitlik için ratedate'i SQL tarafına bırakalım, query'i değiştirelim.
                            batch_data.append((user_id, product_id, score))
                    
                    # --- TOPLU GÖNDERİM ZAMANI ---
                    if batch_data:
                        # execute_values çok hızlıdır
                        extras.execute_values(
                            cursor, 
                            """INSERT INTO productrating (userid, productid, rating, ratedate) 
                               VALUES %s ON CONFLICT (userid, productid) DO NOTHING""",
                            batch_data,
                            template="(%s, %s, %s, NOW())", # NOW() burada kullanılıyor
                            page_size=1000
                        )
                        conn.commit()
                        print(f"-> ✅ {len(batch_data)} oy TEK SEFERDE yüklendi.")
                        total_ratings_inserted += len(batch_data)
                    else:
                        print("-> (Eklenecek veri yok)")
                    
                except Exception as e:
                    print(f"\n   ❌ Dosya hatası: {e}")
                    conn.rollback()

        print(f"\n🏁 İŞLEM TAMAMLANDI! Toplam {total_ratings_inserted} adet oy saniyeler içinde işlendi.")

    except Exception as e:
        print("\n❌ GENEL HATA:", e)
    
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()