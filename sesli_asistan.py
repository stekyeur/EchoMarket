import speech_recognition as sr
from gtts import gTTS
import playsound
import os
import psycopg2
import time
import sys
from config import DB_CONFIG  # Config dosyasını kullanıyoruz

# --- AYARLAR ---
# Bu masaüstü uygulaması olduğu için, şimdilik ID'si 1 olan kullanıcıymış gibi davranacağız.
AKTIF_KULLANICI_ID = 1 

# ----------------------------------------
# 🔊 Sesli Konuşma Fonksiyonu
# ----------------------------------------
def speak(text):
    print(f"🗣 ASİSTAN: {text}")
    try:
        tts = gTTS(text=text, lang='tr')
        filename = "cevap.mp3"
        tts.save(filename)
        playsound.playsound(filename)
        # Dosya kilidini açmak için biraz bekle ve sil
        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        print("Ses hatası (Önemli değil):", e)

# ----------------------------------------
# 🛒 YENİ: Sepete Ekleme (VERİTABANI)
# ----------------------------------------
def sepete_ekle_db(urun_id, urun_adi, miktar=1):
    conn = None
    try:
        params = DB_CONFIG.copy()
        if 'sslmode' not in params: params['sslmode'] = 'prefer'
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()

        # 1. Kullanıcının aktif bir sepeti (ShoppingSession) var mı?
        cursor.execute("SELECT id FROM shoppingsession WHERE userid = %s", (AKTIF_KULLANICI_ID,))
        row = cursor.fetchone()

        if row:
            session_id = row[0]
        else:
            # Yoksa yeni sepet oluştur
            cursor.execute("INSERT INTO shoppingsession (userid) VALUES (%s) RETURNING id", (AKTIF_KULLANICI_ID,))
            session_id = cursor.fetchone()[0]

        # 2. Ürünü sepete ekle (Varsa üzerine ekle - ON CONFLICT)
        sql = """
            INSERT INTO cartitem (sessionid, productid, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (sessionid, productid) 
            DO UPDATE SET quantity = cartitem.quantity + %s;
        """
        cursor.execute(sql, (session_id, urun_id, miktar, miktar))
        
        conn.commit()
        speak(f"{urun_adi} başarıyla veritabanına kaydedildi.")
        
    except Exception as e:
        print("DB Hatası:", e)
        speak("Sepete eklerken veritabanı hatası oluştu.")
    finally:
        if conn: conn.close()

# ----------------------------------------
# 🛒 YENİ: Sepeti Okuma (VIEW KULLANARAK)
# ----------------------------------------
def sepeti_oku_db():
    conn = None
    try:
        params = DB_CONFIG.copy()
        if 'sslmode' not in params: params['sslmode'] = 'prefer'
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()

        # Oluşturduğumuz VIEW sayesinde çok kolay sorgu atıyoruz
        cursor.execute("""
            SELECT product_name, quantity, total_line_price 
            FROM view_cart_details 
            WHERE userid = %s
        """, (AKTIF_KULLANICI_ID,))
        
        urunler = cursor.fetchall()
        
        if not urunler:
            speak("Sepetiniz şu an boş.")
        else:
            speak(f"Sepetinizde {len(urunler)} çeşit ürün var. Sayıyorum:")
            for urun in urunler:
                # Örn: "Makarna, 2 adet, toplam 50 lira"
                mesaj = f"{urun[0]}, {urun[1]} adet. Toplam {urun[2]} lira."
                speak(mesaj)
                time.sleep(1) # Okurken nefes alsın

    except Exception as e:
        print("DB Hatası:", e)
        speak("Sepet bilgilerine ulaşılamadı.")
    finally:
        if conn: conn.close()

# ----------------------------------------
# 🔍 YENİ: Ürün Arama (KATEGORİ VEYA İSİM)
# ----------------------------------------
def urun_ara_db(ses_komutu, siralama="normal"):
    conn = None
    urunler_listesi = []
    
    try:
        params = DB_CONFIG.copy()
        if 'sslmode' not in params: params['sslmode'] = 'prefer'
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()

        # Gereksiz kelimeleri temizle
        aranan = ses_komutu.replace("getir", "").replace("bul", "").replace("ürünleri", "").replace("listele", "").strip()

        # SQL Sorgusu (Hem kategori adına hem ürün adına bakar)
        base_sql = """
            SELECT p.id, p.name, p.price 
            FROM product p
            LEFT JOIN category c ON p.categoryid = c.id
            WHERE p.name ILIKE %s OR c.name ILIKE %s
        """
        
        if siralama == "ucuz":
            base_sql += " ORDER BY p.price ASC LIMIT 5"
        else:
            base_sql += " LIMIT 5"

        term = f"%{aranan}%"
        cursor.execute(base_sql, (term, term))
        urunler_listesi = cursor.fetchall()

    except Exception as e:
        print("Arama Hatası:", e)
    finally:
        if conn: conn.close()
        
    return urunler_listesi, aranan

# ----------------------------------------
# 🎧 ANA PROGRAM
# ----------------------------------------
r = sr.Recognizer()

# Başlarken veritabanı bağlantısını test edelim
speak("Sistem başlatılıyor. Veritabanına bağlanılıyor...")

while True:
    try:
        speak("Ana menüdesiniz. 1 Ürün bul, 2 Sepetimi oku, 3 Çıkış.")
        
        with sr.Microphone() as source:
            print("🎧 Dinliyorum...")
            # Gürültü azaltmayı kısalttık
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        
        try:
            secim = r.recognize_google(audio, language="tr-TR").lower()
            print(f"Algılanan: {secim}")
        except sr.UnknownValueError:
            speak("Ses gelmedi.")
            continue

        # --- 1. ÜRÜN ARAMA ---
        if "1" in secim or "ürün" in secim or "bul" in secim or "al" in secim:
            speak("Hangi ürünü veya kategoriyi istersiniz?")
            
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio_ara = r.listen(source)
            
            try:
                komut_ara = r.recognize_google(audio_ara, language="tr-TR").lower()
                print(f"Aranan: {komut_ara}")
                
                # En ucuz isteği var mı?
                mod = "ucuz" if "ucuz" in komut_ara else "normal"
                
                bulunanlar, aranan_kelime = urun_ara_db(komut_ara, mod)
                
                if not bulunanlar:
                    speak("Maalesef bununla ilgili bir ürün bulamadım.")
                    continue
                
                speak(f"{aranan_kelime} için bulduklarım:")
                
                # Ürünleri Say
                for i, (uid, uad, ufiyat) in enumerate(bulunanlar, 1):
                    speak(f"{i}. {uad}, {ufiyat} lira.")
                    time.sleep(0.5)
                
                # Seçim Yap
                speak("Hangisini sepete ekleyelim? Birinci, ikinci veya iptal diyebilirsiniz.")
                
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio_sec = r.listen(source)
                
                secim_txt = r.recognize_google(audio_sec, language="tr-TR").lower()
                
                secilen_index = -1
                if "bir" in secim_txt or "1" in secim_txt: secilen_index = 0
                elif "iki" in secim_txt or "2" in secim_txt: secilen_index = 1
                elif "üç" in secim_txt or "3" in secim_txt: secilen_index = 2
                elif "dört" in secim_txt or "4" in secim_txt: secilen_index = 3
                elif "beş" in secim_txt or "5" in secim_txt: secilen_index = 4
                
                if secilen_index != -1 and secilen_index < len(bulunanlar):
                    p_id, p_name, p_price = bulunanlar[secilen_index]
                    sepete_ekle_db(p_id, p_name) # Veritabanına kaydet
                else:
                    speak("İşlem iptal edildi.")

            except sr.UnknownValueError:
                speak("Dediğinizi anlayamadım.")

        # --- 2. SEPETE BAK ---
        elif "2" in secim or "sepet" in secim:
            sepeti_oku_db() # Veritabanından oku

        # --- 3. ÇIKIŞ ---
        elif "çıkış" in secim or "kapat" in secim or "4" in secim:
            speak("Görüşmek üzere.")
            sys.exit()

    except Exception as e:
        print("Hata:", e)
        # Hata olunca döngü kırılmasın, devam etsin
        time.sleep(1)