import psycopg2
# config.py dosyasından DB_CONFIG sözlüğünü içe aktarıyoruz
# Not: config.py ile UpdateStock.py aynı klasörde olmalıdır.
from config import DB_CONFIG 

def update_stocks_randomly():
    print("\n--- STOK GÜNCELLEME İŞLEMİ (Config Kullanılıyor) ---")
    
    conn = None
    try:
        # Bağlantı parametrelerini hazırlayalım
        # config.py'deki bilgilerin kopyasını alıyoruz ki orijinali bozulmasın
        connect_params = DB_CONFIG.copy()
        
        # Supabase bağlantısı için SSL modu genelde gereklidir.
        # Eğer config.py içinde yoksa burada ekliyoruz.
        if 'sslmode' not in connect_params:
            connect_params['sslmode'] = 'prefer'

        print(f"Bağlanılıyor: {connect_params['host']}...")

        # **connect_params yapısı, sözlükteki anahtarları (host, user vb.) 
        # otomatik olarak fonksiyona dağıtır.
        conn = psycopg2.connect(**connect_params)
        
        cursor = conn.cursor()
        print("✅ Veritabanına başarıyla bağlanıldı.")

        # --- SQL KOMUTU ---
        # random() * 51 -> 0 ile 50.99 arası sayı üretir
        # floor() -> Aşağı yuvarlar (0, 1, ... 50)
        sql = "UPDATE product SET stock = floor(random() * 51);"
        
        print("🔄 Stoklar güncelleniyor...")
        cursor.execute(sql)
        
        # Kaç satırın etkilendiğini al
        updated_rows = cursor.rowcount
        
        conn.commit()
        print(f"✅ İŞLEM TAMAMLANDI! Toplam {updated_rows} ürünün stoğu rastgele değiştirildi.")

    except Exception as e:
        print("\n❌ HATA OLUŞTU:")
        print(e)
        print("-" * 30)
        print("İPUCU: Eğer 'Tenant or user not found' hatası alırsan;")
        print("config.py dosyasındaki 'port' değerini '6543' yapmayı dene.")
    
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    update_stocks_randomly()