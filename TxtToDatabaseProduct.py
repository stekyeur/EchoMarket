import os
import pandas as pd
import psycopg2

# --- AYARLAR ---
DOSYA_KLASORU = r"C:\Users\arzuf\OneDrive\Belgeler\GitHub\EchoMarket\txtler"

# --- SUPABASE BAĞLANTI BİLGİLERİ (MANUEL) ---
# Supabase'in verdiği yapıyı kullanıyoruz ama .env ile uğraşmamak için
# bilgileri buraya doğrudan yazıyoruz.
USER = "postgres.zhulbmvyuszolutbthpu"  # Proje ID'si eklenmiş tam kullanıcı adı
PASSWORD = "RYca&61au.aMk2//307"             # Senin şifren
HOST = "aws-1-ap-southeast-2.pooler.supabase.com"
PORT = "6543"                             # pgAdmin'de çalışan port
DBNAME = "postgres"

# --- YARDIMCI FONKSİYON ---
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

# --- ANA İŞLEM ---
def veri_aktar():
    print("--- BAĞLANTI KURULUYOR ---")
    print(f"Host: {HOST}")
    print(f"User: {USER}")
    
    conn = None
    try:
        # Supabase'in verdiği bağlantı yöntemi
        conn = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME,
            sslmode='require' # Güvenlik için ekledik
        )
        print("✅ Connection successful! (Bağlantı Başarılı)")
        
        cursor = conn.cursor()

        # Klasör kontrolü
        if not os.path.exists(DOSYA_KLASORU):
            print(f"❌ Klasör bulunamadı: {DOSYA_KLASORU}")
        else:
            print("📂 Dosyalar taranıyor...")
            sayac = 0
            
            for dosya_adi in os.listdir(DOSYA_KLASORU):
                if dosya_adi.endswith(".txt"):
                    print(f"📄 İşleniyor: {dosya_adi}")
                    
                    # 1. Kategori Ekleme
                    kategori_adi = dosya_adi.replace(".txt", "")
                    
                    # Kategori var mı?
                    cursor.execute("SELECT ID FROM Category WHERE Name = %s", (kategori_adi,))
                    kategori_id = cursor.fetchone()
                    
                    if not kategori_id:
                        try:
                            cursor.execute("INSERT INTO Category (Name) VALUES (%s) RETURNING ID", (kategori_adi,))
                            kategori_id = cursor.fetchone()[0]
                            conn.commit() # Kategoriyi hemen kaydet
                            print(f"   -> Yeni Kategori: {kategori_adi}")
                        except Exception as e:
                            conn.rollback()
                            print(f"   -> Hata: {e}")
                            continue
                    else:
                        kategori_id = kategori_id[0]

                    # 2. Ürünleri Ekleme
                    dosya_yolu = os.path.join(DOSYA_KLASORU, dosya_adi)
                    try:
                        df = pd.read_csv(dosya_yolu, on_bad_lines='skip')
                        dosya_ici_sayac = 0
                        
                        for index, row in df.iterrows():
                            urun_adi = row.get('Name')
                            if pd.isna(urun_adi): continue

                            fiyat = fiyat_temizle(row.get('Price'))
                            
                            cursor.execute("""
                                INSERT INTO Product (Name, Description, Price, Stock, CategoryID, UnitOfMeasure)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (urun_adi, str(urun_adi), fiyat, 50, kategori_id, 'Adet'))
                            
                            dosya_ici_sayac += 1
                            sayac += 1
                        
                        conn.commit() # Dosya bitince kaydet
                        print(f"   ✅ {dosya_ici_sayac} ürün eklendi.")
                        
                    except Exception as e:
                        print(f"   -> Dosya hatası: {e}")
                        conn.rollback()

            print(f"\n🏁 İşlem Tamam! Toplam {sayac} ürün veritabanına yüklendi.")

        cursor.close()
        conn.close()
        print("Connection closed.")

    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    veri_aktar()