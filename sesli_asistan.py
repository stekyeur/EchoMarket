import speech_recognition as sr
from gtts import gTTS
import playsound
import os
import psycopg2
import time
import sys # Programdan çıkış için gerekli

# ----------------------------------------
# 🔊 Sesli konuşma fonksiyonu
# ----------------------------------------
def speak(text):
    print(f"🗣 ASİSTAN: {text}")
    try:
        tts = gTTS(text=text, lang='tr')
        # Dosya çakışmasını önlemek için rastgele isimlendirme veya bekleme yapılabilir
        # Basitlik adına overwrite mantığı kullanıyoruz
        filename = "cevap.mp3"
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)
    except Exception as e:
        print("Ses hatası:", e)

# ----------------------------------------
# 🛒 Sepete Ekleme Fonksiyonu
# ----------------------------------------
def sepete_ekle(urun_adi, fiyat, urun_id):
    try:
        with open("sepetim.txt", "a", encoding="utf-8") as f:
            f.write(f"ID: {urun_id} - {urun_adi} - {fiyat}\n")
        speak(f"{urun_adi} sepete eklendi.")
    except Exception as e:
        print("Dosya yazma hatası:", e)
        speak("Sepete eklerken bir hata oluştu.")

# ----------------------------------------
# 🗄 PostgreSQL Bağlantısı
# ----------------------------------------
DB_CONFIG = {
    "host": "aws-1-ap-southeast-2.pooler.supabase.com",
    "port": "5432",
    "dbname": "postgres",
    "user": "postgres.zhulbmvyuszoiutbthpu",
    "password": "jGF6nkMVNK9rAxYk" # ŞİFRENİ BURAYA YAZMAYI UNUTMA
}

def get_all_products_by_category(category_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM category WHERE LOWER(name) = LOWER(%s)", (category_name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return []
        category_id = row[0]
        # Varsayılan sıralama
        cursor.execute("SELECT id, name, price FROM product WHERE categoryid = %s", (category_id,))
        products = cursor.fetchall() 
        conn.close()
        return products
    except Exception as e:
        print("SQL Hatası:", e)
        return []

def get_the_cheapest(category_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM category WHERE LOWER(name) = LOWER(%s)", (category_name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return []
        category_id = row[0]
        # DÜZELTME: En ucuz için ASC (Artan) sıralama kullanılır.
        cursor.execute("SELECT id, name, price FROM product WHERE categoryid = %s ORDER BY price ASC", (category_id,))
        products = cursor.fetchall() 
        conn.close()
        return products
    except Exception as e:
        print("SQL Hatası:", e)
        return []

# --- KATEGORİ LİSTELERİ ---
kahvaltilik_urunler = ["yumurta","peynir","zeytin","reçel","bal","tereyağı","kaşar","salam","sucuk","sosis","kreması","ekmek","labne","yoğurt"]
atistirmaliklar = ["çıtır çerez","popcorn","kuru yemiş karışık","mini kraker","atıştırmalık","atıştırma"]
agiz_bakim = ["diş macunu","diş fırçası","ağız gargarası","diş ipi","diş","ağız","dil"]
banyo_urunleri = ["duş jeli","şampuan","sabun","banyo lifi","lif","banyo","duş","vücut","losyon"]
bulasik_makinesi_deterjani = ["bulaşık makinesi kapsülü","toz deterjan","parlatıcı","makine tuzu"]
bulasik_yikama = ["elde bulaşık deterjanı","sünger","bulaşık teli","bulaşık deterjanı"]
deodorant = ["roll-on","sprey deodorant","stick deodorant","deodorant"]
gazsiz_icecek = ["meyve suyu","limonata","soğuk çay","gazsız içecek","ice tea","salep","kaynak suyu","toz içecek","milkshake","oralet"]
hazir_corba = ["domates çorbası","mercimek çorbası","mantar çorbası","hazır çorba","çorba"]
kahvaltilik_gevrek = ["corn flakes","yulaf ezmesi","granola","gevrek","tahıl gevreği"]
kahve = ["türk kahvesi","filtre kahve","espresso","3ü1 arada","latte","cappuciono","kahve","kahvesi"]
kagit_havlu = ["kağıt havlu rulo","çok amaçlı havlu","kağıt havlu"]
konserveler = ["ton balığı","mısır konservesi","bezelye konservesi","konservesi"]
kuru_gida = ["pirinç","bulgur","mercimek","nohut","fasulye","mantı","baharat","tarhana","kurusu","harcı","sos"]
kuruyemis = ["fındık","badem","fıstık","kaju","karışık kuruyemiş","kuruyemiş","çekirdek","ceviz","ayçekirdeği"]
makarna = ["spagetti","burgu makarna","penne","fiyonk","makarna","erişte","noodle"]
mutfak_banyo_temizlik = ["çamaşır suyu","yüzey temizleyici","banyo temizleyici","fayans","duşakabin","mutfak temizleyici","lavabo açıcı","yağ temizleyici","kireç","gider","fırın","ocak","sarı güç"]
sac_bakimi = ["şampuan","saç kremi","saç maskesi","saç yağı","dökülme","saç","keratin","tarak"]
sivi_yaglar = ["zeytinyağı","ayçiçek yağı","mısır yağı"]
toz_seker = ["toz şekeri","pudra şekeri"]
tiras_urunleri = ["tıraş köpüğü","tıraş bıçağı","tıraş sonrası losyon","tıraş"]
unlu_mamul = ["poğaça","simit","börek","çörek","kömbe","kurabiye","katmer"]
camasir_deterjani = ["toz deterjan","sıvı deterjan","kapsül deterjan"]
camasir_yikama_urunleri = ["leke çıkarıcı","renk koruyucu","çamaşır filesi","deterjan"]

kategoriler = {
    "Kahvaltılıklar": kahvaltilik_urunler,
    "Atıştırmalıklar": atistirmaliklar,
    "Ağız Bakım": agiz_bakim,
    "Banyo Ürünleri": banyo_urunleri,
    "Bulaşık Makinesi Deterjanı": bulasik_makinesi_deterjani,
    "Bulaşık Yıkama": bulasik_yikama,
    "Deodorant": deodorant,
    "Gazsız İçecek": gazsiz_icecek,
    "Hazır Çorba": hazir_corba,
    "Kahvaltılık Gevrek": kahvaltilik_gevrek,
    "Kahve": kahve,
    "Kağıt Havlu": kagit_havlu,
    "Konserveler": konserveler,
    "Kuru Gıda": kuru_gida,
    "Kuruyemiş": kuruyemis,
    "Makarna": makarna,
    "Mutfak Banyo Temizlik": mutfak_banyo_temizlik,
    "Saç Bakımı": sac_bakimi,
    "Sıvı Yağlar": sivi_yaglar,
    "Toz Şeker": toz_seker,
    "Tıraş Ürünleri": tiras_urunleri,
    "Unlu Mamul": unlu_mamul,
    "Çamaşır Deterjanı": camasir_deterjani,
    "Çamaşır Yıkama Ürünleri": camasir_yikama_urunleri,
    "Çikolata": ["çikolata"],
    "Çay": ["çay"],
    "Süt": ["süt"],
    "Kek": ["kek"],
    "Protein Bar": ["protein bar"],
    "Salça": ["salça"],
    "Tuvalet Kağıdı": ["tuvalet kağıdı"],
    "Yumuşatıcı": ["yumuşatıcı"],
    "Un": ["un"],
}

kategori_eslestirme = {
    k: k.title().replace("ı","I").replace("ç","Ç").replace("ş","Ş").replace("ö","Ö").replace("ü","Ü")
    for k in kategoriler
}

# ----------------------------------------
# 🎧 ANA PROGRAM
# ----------------------------------------

r = sr.Recognizer()

while True: # ANA DÖNGÜ
    try:
        speak("Merhabalar, ana menüdesiniz. Ne yapmak istersiniz? 1 Ürün al, 2 Sepete bak, 3 Ayarlar, 4 Çıkış")
        
        with sr.Microphone() as source:
            print("🎧 Dinliyorum (Ana Menü)...")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
        
        try:
            menü_komut = r.recognize_google(audio, language="tr-TR").lower()
            print(f"Algılanan Menü Komutu: {menü_komut}")
        except sr.UnknownValueError:
            speak("Anlayamadım, tekrar eder misiniz?")
            continue

        # ---------------------------
        # 1. ÜRÜN ARAMA MENÜSÜ
        # ---------------------------
        if "1" in menü_komut or "bir" in menü_komut or "ilk" in menü_komut or "ürün" in menü_komut:
            speak("Merhabalar, ne almak istiyorsunuz?")
            
            with sr.Microphone() as source:
                print("🎧 Dinliyorum (Ürün İsteği)...")
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source)

            try:
                komut = r.recognize_google(audio, language="tr-TR").lower()
            except sr.UnknownValueError:
                speak("Anlayamadım, tekrar söyler misin?")
                continue

            print("Kullanıcı isteği:", komut)

            # Bağlaç temizliği
            for kelime in [" ve ", " ile ", " da ", " de ", ","]:
                komut = komut.replace(kelime, " ")

            bulunan_kategori = None
            for py_kat, sql_kat in kategori_eslestirme.items():
                for anahtar_kelime in kategoriler[py_kat]:
                    if anahtar_kelime in komut:
                        bulunan_kategori = sql_kat
                        break
                if bulunan_kategori:
                    break

            if bulunan_kategori:
                # --- LOOP: KATEGORİ ONAY ---
                onay_alindi = False
                en_ucuz = False
                ana_menuye_don = False # İç döngülerden tamamen çıkmak için bayrak
                
                while True:
                    speak(f"{bulunan_kategori} kategorisi bulundu. Listeleyeyim mi? Evet, hayır veya en ucuz diyebilirsiniz.")
                    with sr.Microphone() as source:
                        r.adjust_for_ambient_noise(source)
                        audio_onay = r.listen(source)
                    try:
                        cevap = r.recognize_google(audio_onay, language="tr-TR").lower()
                        print(f"Onay Cevabı: {cevap}")

                        if "evet" in cevap or "uygun" in cevap or "listele" in cevap:
                            onay_alindi = True
                            break
                        elif "hayır" in cevap or "istemiyorum" in cevap:
                            speak("Tamam, iptal ettim.")
                            break
                        elif "en ucuz" in cevap or "ucuz" in cevap:
                            speak("Tamam, en ucuzları getiriyorum.")
                            en_ucuz = True
                            onay_alindi = True 
                            break
                        else:
                            speak("Anlayamadım, evet mi hayır mı?")
                    except sr.UnknownValueError:
                        speak("Sesinizi duyamadım.")

                if onay_alindi:
                    speak("Ürünler getiriliyor...")
                    
                    if en_ucuz:
                        tum_urunler = get_the_cheapest(bulunan_kategori)
                    else:
                        tum_urunler = get_all_products_by_category(bulunan_kategori)
                    
                    if not tum_urunler:
                        speak("Bu kategoride veritabanında ürün yok.")
                        continue        
                    
                    # --- ÜRÜN LİSTELEME DÖNGÜSÜ (PAGINATION) ---
                    index = 0
                    while index < len(tum_urunler):
                        # Eğer ana menüye dönme isteği geldiyse bu döngüyü de kır
                        if ana_menuye_don:
                            break

                        sayfa = tum_urunler[index : index + 5]
                        
                        speak(f"İşte ürünler:")
                        for i, (u_id, u_ad, u_fiyat) in enumerate(sayfa, 1):
                            speak(f"{i}. ürün: {u_ad}. Fiyatı: {u_fiyat}")
                            time.sleep(0.5)

                        # --- LOOP: SEÇİM YAPMA ---
                        sayfa_degistir = False 

                        while True:
                            # Eğer ana menüye dönülecekse seçim döngüsünü de kır
                            if ana_menuye_don:
                                break

                            speak("Devam etmek mi istersin, yoksa sepete mi ekleyelim?")
                            with sr.Microphone() as source:
                                r.adjust_for_ambient_noise(source)
                                audio_secim = r.listen(source)
                            
                            try:
                                secim = r.recognize_google(audio_secim, language="tr-TR").lower()
                                print("Seçim:", secim)

                                # SEPETE EKLEME
                                if "sepet" in secim or "almak" in secim or "ekle" in secim:
                                    while True:
                                        speak("Kaçıncı ürünü istiyorsunuz?")
                                        with sr.Microphone() as source:
                                            r.adjust_for_ambient_noise(source)
                                            audio_sayi = r.listen(source)
                                        
                                        try:
                                            kacinci = r.recognize_google(audio_sayi, language="tr-TR").lower()
                                            if "iptal" in kacinci:
                                                speak("İptal edildi.")
                                                break

                                            secilen_index = -1
                                            if "birinci" in kacinci or "1" in kacinci or "ilk" in kacinci: secilen_index = 0
                                            elif "ikinci" in kacinci or "2" in kacinci: secilen_index = 1
                                            elif "üçüncü" in kacinci or "3" in kacinci: secilen_index = 2
                                            elif "dördüncü" in kacinci or "4" in kacinci: secilen_index = 3
                                            elif "beşinci" in kacinci or "5" in kacinci: secilen_index = 4
                                            
                                            if secilen_index != -1 and secilen_index < len(sayfa):
                                                secilen_id, secilen_ad, secilen_fiyat = sayfa[secilen_index]
                                                sepete_ekle(secilen_ad, secilen_fiyat, secilen_id)
                                                
                                                # SIRADAKİ SAYFA ONAYI
                                                while True:
                                                    speak("Sıradaki ürünlere geçelim mi, yoksa bu sayfada kalalım mı? Geç, Kal veya Çıkış diyebilirsiniz.")
                                                    with sr.Microphone() as source:
                                                        audio_devam = r.listen(source)
                                                    try:
                                                        cevap_devam = r.recognize_google(audio_devam, language="tr-TR").lower()
                                                        
                                                        if "geç" in cevap_devam or "sıradaki" in cevap_devam or "evet" in cevap_devam:
                                                            speak("Sıradakilere geçiyorum.")
                                                            index += 5
                                                            sayfa_degistir = True
                                                            break
                                                        
                                                        elif "kal" in cevap_devam or "buradan" in cevap_devam or "hayır" in cevap_devam:
                                                            speak("Tamam, ne yapmak istersin? Sepet mi Devam mı?")
                                                            break
                                                        
                                                        elif "çıkış" in cevap_devam or "bitir" in cevap_devam:
                                                            speak("Ana menüye dönülüyor.")
                                                            ana_menuye_don = True # Flag'i kaldır
                                                            break
                                                        
                                                        else:
                                                            speak("Anlayamadım, geçelim mi kalalım mı?")
                                                    except:
                                                        speak("Duyamadım.")
                                                
                                                # While (Kaçıncı ürün) döngüsünden çık
                                                break 
                                            else:
                                                speak("Lütfen geçerli bir sayı söyleyin.")
                                        except:
                                            speak("Anlayamadım, kaçıncı?")

                                    if ana_menuye_don:
                                        break # Seçim döngüsünden çık
                                    
                                    if sayfa_degistir:
                                        break # Seçim döngüsünden çık (Sayfa değişecek)

                                # SONRAKİ SAYFA (Direkt komutla)
                                elif "devam" in secim or "sonraki" in secim:
                                    index += 5
                                    if index >= len(tum_urunler):
                                        speak("Başka ürün kalmadı. Menüye dönüyorum.")
                                        break 
                                    else:
                                        break # Seçim loop'undan çık (Sayfa değişecek)

                                # ÇIKIŞ
                                elif "hayır" in secim or "çıkış" in secim or "kapat" in secim:
                                    speak("Ana menüye dönülüyor.")
                                    ana_menuye_don = True
                                    break
                                
                                else:
                                    speak("Anlayamadım. Devam mı, sepet mi?")
                            
                            except sr.UnknownValueError:
                                speak("Duyamadım.")
                        
                        # Ürünler bittiyse veya ana menüye dönülecekse döngüyü kır
                        if index >= len(tum_urunler) or ana_menuye_don:
                            break
            else:
                speak("Bu kelimeye uygun kategori bulamadım.")
        
        # ---------------------------
        # 2. SEPETE BAKMA MENÜSÜ
        # ---------------------------
        elif "2" in menü_komut or "iki" in menü_komut or "sepet" in menü_komut:
            speak("Sepetinize bakıyorum...")
            if os.path.exists("sepetim.txt"):
                with open("sepetim.txt", "r", encoding="utf-8") as f:
                    icerik = f.read()
                    if icerik.strip():
                        speak("Sepetinizde şunlar var:")
                        for satir in icerik.split("\n"):
                            if satir.strip():
                                speak(satir)
                    else:
                        speak("Sepetiniz şu an boş.")
            else:
                speak("Henüz bir sepet oluşturmadınız.")

        # ---------------------------
        # 3. KULLANICI AYARLARI
        # ---------------------------
        elif "3" in menü_komut or "üç" in menü_komut or "ayarlar" in menü_komut:
            speak("Kullanıcı ayarları menüsü henüz aktif değil.")

        # ---------------------------
        # 4. ÇIKIŞ
        # ---------------------------
        elif "4" in menü_komut or "çıkış" in menü_komut:
            speak("Çıkış yapılıyor. İyi günler.")
            sys.exit()

        else:
            speak("Geçersiz seçenek, lütfen tekrar deneyin.")

    except Exception as e:
        print("Genel Hata:", e)
        speak("Bir hata oluştu, tekrar başlatıyorum.")