import os
import pandas as pd
import psycopg2
# config.py dosyasından DB_CONFIG'i çekiyoruz
# Not: config.py ile bu dosya aynı klasörde olmalı.
from config import DB_CONFIG

# --- AYARLAR ---
# --- AYARLAR ---
# '..' demek bir üst klasöre çık demektir.
DOSYA_KLASORU = "../Data/txtler" # Klasör yolunu kontrol edin

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
    print("\n--- ÜRÜN AKTARIM (Config ile) ---")
    
    conn = None
    try:
        # Config dosyasındaki ayarları kullanıyoruz
        connect_params = DB_CONFIG.copy()
        if 'sslmode' not in connect_params:
            connect_params['sslmode'] = 'prefer'

        print(f"Bağlanılıyor: {connect_params['host']}...")
        conn = psycopg2.connect(**connect_params)
        cursor = conn.cursor()
        print("✅ Veritabanına başarıyla bağlanıldı.")
    except Exception as e:
        print("❌ BAĞLANTI HATASI:")
        print(e)
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
                    
                    # Veritabanına Ekle (Çift kayıt olmaması için ON CONFLICT ekledik)
                    # Not: ON CONFLICT çalışması için Name alanının unique olması gerekir, 
                    # değilse bile bu kod hata vermeden çalışır.
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