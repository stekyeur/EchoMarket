import os
import pandas as pd
import psycopg2
import bcrypt
# config.py dosyasından DB_CONFIG'i çekiyoruz
from config import DB_CONFIG

# --- AYARLAR ---
DOSYA_KLASORU = r"C:\Users\arzuf\OneDrive\Belgeler\GitHub\EchoMarket\txt_2"
KULLANICI_DOSYASI = "kullanici_verileri.txt"
ADRES_DOSYASI = "address_data.txt"

# --- ŞİFRELEME FONKSİYONU ---
def hash_password(plain_password):
    if pd.isna(plain_password): return ""
    password_bytes = str(plain_password).encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def veri_aktar_user_address():
    print("\n--- KULLANICI VE ADRES YÜKLEME (Config ile) ---")
    
    conn = None
    try:
        # Config dosyasındaki ayarları kullanıyoruz
        # Eğer sslmode eksikse ekliyoruz
        connect_params = DB_CONFIG.copy()
        if 'sslmode' not in connect_params:
            connect_params['sslmode'] = 'prefer'

        conn = psycopg2.connect(**connect_params)
        cursor = conn.cursor()
        print("✅ Veritabanı bağlantısı başarılı!\n")
    except Exception as e:
        print("❌ BAĞLANTI HATASI:", e)
        return

    # 1. KULLANICILARI YÜKLE
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
                    
                    # Şifreleme işlemi
                    ham_sifre = row['Password']
                    val_pass = hash_password(ham_sifre)
                    
                    val_phone = str(row['Phone']) if has_phone and pd.notna(row['Phone']) else None

                    cursor.execute("""
                        INSERT INTO "user" (id, name, email, password, phone)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (val_id, val_name, val_email, val_pass, val_phone))
                    sayac += 1
                except:
                    continue

            conn.commit()
            print(f"   ✅ {sayac} kullanıcı şifrelenerek eklendi.")
            
            try:
                cursor.execute('SELECT setval(pg_get_serial_sequence(\'"user"\', \'id\'), (SELECT MAX(id) FROM "user") + 1)')
                conn.commit()
            except:
                conn.rollback()

        except Exception as e:
            print(f"   ❌ Kullanıcı hatası: {e}")
            conn.rollback()

    print("-" * 30)

    # 2. ADRESLERİ YÜKLE
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
                except: continue 

                cursor.execute('SELECT 1 FROM "user" WHERE id = %s', (val_user_id,))
                if not cursor.fetchone(): continue 

                cursor.execute("""
                    INSERT INTO address (userid, street, city, zipcode)
                    VALUES (%s, %s, %s, %s)
                """, (val_user_id, val_street, val_city, val_zip))
                sayac += 1

            conn.commit()
            print(f"   ✅ {sayac} adres eklendi.")

        except Exception as e:
            print(f"   ❌ Adres hatası: {e}")
            conn.rollback()

    if conn:
        cursor.close()
        conn.close()
        print("\n🏁 İŞLEM TAMAMLANDI.")

if __name__ == "__main__":
    veri_aktar_user_address()