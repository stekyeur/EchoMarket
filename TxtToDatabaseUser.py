import os
import pandas as pd
import psycopg2

# --- AYARLAR ---
DOSYA_KLASORU = r"C:\Users\arzuf\OneDrive\Belgeler\GitHub\EchoMarket\txt_2"
KULLANICI_DOSYASI = "kullanici_verileri.txt"
ADRES_DOSYASI = "address_data.txt"

# --- BAĞLANTI BİLGİLERİ ---
DB_CONFIG = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",          
    "port": "5432",
    "dbname": "postgres",
    "user": "postgres.zhulbmvyuszoiutbthpu", 
    "password": "RYca&61au.aMk2//307"

}

def veri_aktar_user_address():
    print("\n--- KULLANICI VE ADRES YÜKLEME (FIXED TRANSACTION) ---")
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Veritabanı bağlantısı başarılı!\n")
    except Exception as e:
        print("❌ BAĞLANTI HATASI:", e)
        return

    # ---------------------------------------------------------
    # 1. KULLANICILARI YÜKLE
    # ---------------------------------------------------------
    kullanici_yolu = os.path.join(DOSYA_KLASORU, KULLANICI_DOSYASI)
    if os.path.exists(kullanici_yolu):
        print(f"👤 İşleniyor: {KULLANICI_DOSYASI}")
        try:
            df_user = pd.read_csv(kullanici_yolu)
            has_phone = 'Phone' in df_user.columns
            
            sayac = 0
            for _, row in df_user.iterrows():
                try:
                    val_id = int(row['id'])
                    val_name = str(row['Name'])
                    val_email = str(row['Email'])
                    val_pass = str(row['Password'])
                    
                    if has_phone and pd.notna(row['Phone']):
                        val_phone = str(row['Phone'])
                    else:
                        val_phone = None 
                        
                except Exception as type_err:
                    print(f"   ⚠️ Veri hatası: {type_err}")
                    continue

                cursor.execute("""
                    INSERT INTO "user" (id, name, email, password, phone)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (val_id, val_name, val_email, val_pass, val_phone))
                
                sayac += 1

            conn.commit()
            print(f"   ✅ {sayac} kullanıcı işlendi (Zaten varsa atlandı).")
            
            # ID SAYACI GÜNCELLEME (HATAYI ÇÖZEN KISIM)
            try:
                # Sequence adını bulmaya çalışalım (Genellikle user_id_seq veya "User_id_seq")
                # Önce basit bir SQL ile max ID'yi set edelim, sequence adını PostgreSQL otomatik bulsun
                cursor.execute("SELECT setval(pg_get_serial_sequence('\"user\"', 'id'), (SELECT MAX(id) FROM \"user\") + 1)")
                conn.commit()
                print("   🔄 User ID sayacı güncellendi.")
            except Exception as seq_err:
                conn.rollback() # <--- İŞTE BU SATIR HAYAT KURTARIR!
                print(f"   ℹ️ ID sayacı güncellenemedi (Sorun değil, işlem temizlendi): {seq_err}")

        except Exception as e:
            print(f"   ❌ Kullanıcı yükleme hatası: {e}")
            conn.rollback()
    else:
        print(f"⚠️ Dosya bulunamadı: {KULLANICI_DOSYASI}")

    print("-" * 30)

    # ---------------------------------------------------------
    # 2. ADRESLERİ YÜKLE
    # ---------------------------------------------------------
    adres_yolu = os.path.join(DOSYA_KLASORU, ADRES_DOSYASI)
    if os.path.exists(adres_yolu):
        print(f"🏠 İşleniyor: {ADRES_DOSYASI}")
        try:
            df_adres = pd.read_csv(adres_yolu)
            sayac = 0

            for _, row in df_adres.iterrows():
                try:
                    val_user_id = int(row['UserID'])
                    val_street = str(row['Street'])
                    val_city = str(row['City'])
                    val_zip = str(row['ZipCode'])
                except:
                    continue 

                # Kullanıcı kontrolü
                cursor.execute('SELECT 1 FROM "user" WHERE id = %s', (val_user_id,))
                if not cursor.fetchone():
                    continue 

                cursor.execute("""
                    INSERT INTO address (userid, street, city, zipcode)
                    VALUES (%s, %s, %s, %s)
                """, (val_user_id, val_street, val_city, val_zip))
                
                sayac += 1

            conn.commit()
            print(f"   ✅ {sayac} adres başarıyla eklendi.")

        except Exception as e:
            print(f"   ❌ Adres yükleme hatası: {e}")
            conn.rollback()
    else:
        print(f"⚠️ Dosya bulunamadı: {ADRES_DOSYASI}")

    if conn:
        cursor.close()
        conn.close()
        print("\n🏁 İŞLEM TAMAMLANDI.")

if __name__ == "__main__":
    veri_aktar_user_address()