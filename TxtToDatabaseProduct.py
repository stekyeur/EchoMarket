
import os
import pandas as pd
import psycopg2

# --- AYARLAR ---
DOSYA_KLASORU = r"C:\Users\arzuf\OneDrive\Belgeler\GitHub\EchoMarket\txt"

# --- CERRAHİ MÜDAHALE: DOĞRUDAN IP BAĞLANTISI ---
# 1. Host: İsim yerine doğrudan IP adresini yazıyoruz (DNS hatasını aşar).
# 2. User: 'postgres' yazıyoruz (Doğrudan bağlantıda uzun isme gerek yoktur, Tenant hatasını aşar).
# 3. SSL: 'prefer' yapıyoruz (IP ile bağlandığımızda sertifika ismi uyuşmazlığı olmasın diye).

DB_CONFIG = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",      # <-- DNS'i bypass ediyoruz (Loglardan aldığımız IP)
    "port": "5432",
    "dbname": "postgres",
    "user": "postgres.zhulbmvyuszoiutbthpu",           # <-- Sadece 'postgres' (Tenant hatasını çözer)
    "password": "RYca&61au.aMk2//307", 
              # <-- 'require' yerine 'prefer' (IP bağlantısı için şart)
}

# --- TEMİZLİK FONKSİYONLARI ---
def fiyat_temizle(fiyat_str):
    if pd.isna(fiyat_str) or fiyat_str == '' or str(fiyat_str).strip() == ',,':
        return 0.0
    temiz = str(fiyat_str)
    temiz = temiz.replace('TL', '').replace('"', '').strip()
    temiz = temiz.replace('.', '').replace(',', '.')
    try:
        return float(temiz)
    except ValueError:
        return 0.0

def veri_aktar():
    print("\n--- DOĞRUDAN IP BAĞLANTISI DENEMESİ ---")
    print(f"Hedef IP: {DB_CONFIG['host']}")
    print("Durum: DNS ve Pooler devre dışı bırakıldı, doğrudan bağlanılıyor...")
    
    conn = None
    try:
        # Bağlantıyı kur
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("\n✅ BAŞARILI! Veritabanına bağlandık.")
        print("   Bu yöntemle tüm engelleri aştık.\n")
    except Exception as e:
        print("\n❌ BAĞLANTI HATASI:")
        print(e)
        print("\nNOT: Eğer bu da çalışmazsa, IP adresi değişmiş olabilir.")
        print("pgAdmin'de 'Connection' sekmesinde yazan IP adresini kontrol edelim.")
        return

    # Klasör kontrolü
    if not os.path.exists(DOSYA_KLASORU):
        print(f"❌ HATA: Klasör bulunamadı: {DOSYA_KLASORU}")
        return

    toplam_eklenen = 0
    dosya_sayisi = 0

    print("📂 Dosyalar işleniyor...")

    for dosya_adi in os.listdir(DOSYA_KLASORU):
        if dosya_adi.endswith(".txt"):
            dosya_sayisi += 1
            print(f"📄 Dosya: {dosya_adi}")
            
            # 1. KATEGORİ
            kategori_adi = dosya_adi.replace(".txt", "")
            
            # ID Bulma/Ekleme
            cursor.execute("SELECT ID FROM Category WHERE Name = %s", (kategori_adi,))
            kategori_id = cursor.fetchone()
            
            if not kategori_id:
                try:
                    cursor.execute("INSERT INTO Category (Name) VALUES (%s) RETURNING ID", (kategori_adi,))
                    kategori_id = cursor.fetchone()[0]
                    conn.commit()
                    print(f"   ➕ Yeni Kategori: {kategori_adi}")
                except Exception as k_err:
                    conn.rollback()
                    print(f"   ⚠️ Kategori Hatası: {k_err}")
                    continue
            else:
                kategori_id = kategori_id[0]

            # 2. ÜRÜNLER
            dosya_yolu = os.path.join(DOSYA_KLASORU, dosya_adi)
            try:
                df = pd.read_csv(dosya_yolu, on_bad_lines='skip')
                sayac = 0
                
                for _, row in df.iterrows():
                    urun_adi = row.get('Name')
                    if pd.isna(urun_adi): continue

                    fiyat = fiyat_temizle(row.get('Price'))
                    
                    cursor.execute("""
                        INSERT INTO Product (Name, Description, Price, Stock, CategoryID, UnitOfMeasure)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (urun_adi, str(urun_adi), fiyat, 50, kategori_id, 'Adet'))
                    
                    sayac += 1
                
                conn.commit()
                print(f"   ✅ {sayac} ürün eklendi.")
                toplam_eklenen += sayac
                
            except Exception as e:
                print(f"   ❌ Dosya işleme hatası: {e}")
                conn.rollback()

    if conn:
        cursor.close()
        conn.close()

    if dosya_sayisi == 0:
        print("\n⚠️ Klasörde .txt dosyası bulunamadı.")
    else:
        print(f"\n🏁 İŞLEM TAMAMLANDI! Toplam {toplam_eklenen} ürün yüklendi.")

if __name__ == "__main__":
    veri_aktar()