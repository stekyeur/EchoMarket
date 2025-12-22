import os
import pandas as pd
import psycopg2
from psycopg2 import extras
import random
# config.py dosyasından DB_CONFIG'i çekiyoruz
from config import DB_CONFIG

# --- AYARLAR ---
DOSYA_KLASORU = r"C:\Users\betul\Documents\GitHub\EchoMarket\EchoMarket\txt_2"

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
    print("\n--- PRODUCT RATING OLUŞTURUCU (TURBO MOD 🚀 - Config ile) ---")
    
    conn = None
    try:
        # Config dosyasındaki ayarları kullanıyoruz
        # Eğer sslmode eksikse ekliyoruz
        connect_params = DB_CONFIG.copy()
        if 'sslmode' not in connect_params:
            connect_params['sslmode'] = 'prefer'

        conn = psycopg2.connect(**connect_params)
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
                            # (userid, productid, rating) formatında ekliyoruz.
                            # ratedate için SQL tarafında NOW() kullanacağız.
                            batch_data.append((user_id, product_id, score))
                    
                    # --- TOPLU GÖNDERİM ZAMANI ---
                    if batch_data:
                        # execute_values çok hızlıdır
                        extras.execute_values(
                            cursor, 
                            """INSERT INTO productrating (userid, productid, rating, ratedate) 
                               VALUES %s ON CONFLICT (userid, productid) DO NOTHING""",
                            batch_data,
                            template="(%s, %s, %s, NOW())", 
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