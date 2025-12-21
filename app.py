from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import speech_recognition as sr
import psycopg2
import bcrypt
from config import DB_CONFIG


CURRENT_STATE = "MAIN_MENU"
LAST_CATEGORY = None
app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar"

# --- VERİTABANI BAĞLANTISI ---
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, sslmode='require')
    return conn

# --- YARDIMCI: Sepet Sayısını Getir ---
def get_cart_count(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Önce kullanıcının aktif sepet oturumunu bul
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (user_id,))
        session_row = cur.fetchone()

        if session_row:
            session_id = session_row[0]
            # Sepetteki toplam ürün adedini topla
            cur.execute('SELECT SUM(quantity) FROM cartitem WHERE sessionid = %s', (session_id,))
            result = cur.fetchone()
            count = result[0] if result and result[0] else 0
            return int(count)
        return 0
    except Exception as e:
        print(f"Sayaç Hatası: {e}")
        return 0
    finally:
        conn.close()

# Kategori Listesi
kategoriler = {
    "Kahvaltılık": ["yumurta","peynir","zeytin","reçel","bal","tereyağı","kaşar","salam","sucuk","sosis","kreması","ekmek","labne","yoğurt"],
    "Atıştırmalık": ["çıtır çerez","popcorn","kuru yemiş karışık","mini kraker","atıştırmalık","atıştırma"],
    "Ağız Bakım": ["diş macunu","diş fırçası","ağız gargarası","diş ipi","diş","ağız","dil"],
    "Banyo Ürünleri": ["duş jeli","şampuan","sabun","banyo lifi","lif","banyo","duş","vücut","losyon"],
    "Bulaşık Makinesi Deterjanı": ["bulaşık makinesi kapsülü","toz deterjan","parlatıcı","makine tuzu"],
    "Bulaşık Yıkama": ["elde bulaşık deterjanı","sünger","bulaşık teli","bulaşık deterjanı"],
    "Deodorant": ["roll-on","sprey deodorant","stick deodorant","deodorant"],
    "Gazsız İçecek": ["meyve suyu","limonata","soğuk çay","gazsız içecek","ice tea","salep","kaynak suyu","toz içecek","milkshake","oralet"],
    "Hazır Çorba": ["domates çorbası","mercimek çorbası","mantar çorbası","hazır çorba","çorba"],
    "Kahvaltılık Gevrek": ["corn flakes","yulaf ezmesi","granola","gevrek","tahıl gevreği"],
    "Kahve": ["türk kahvesi","filtre kahve","espresso","3ü1 arada","latte","cappuciono","kahve","kahvesi"],
    "Kağıt Havlu": ["kağıt havlu rulo","çok amaçlı havlu","kağıt havlu"],
    "Konserveler": ["ton balığı","mısır konservesi","bezelye konservesi","konservesi"],
    "Kuru Gıda": ["pirinç","bulgur","mercimek","nohut","fasulye","mantı","baharat","tarhana","kurusu","harcı","sos"],
    "Kuruyemiş": ["fındık","badem","fıstık","kaju","karışık kuruyemiş","kuruyemiş","çekirdek","ceviz","ayçekirdeği"],
    "Makarna": ["spagetti","burgu makarna","penne","fiyonk","makarna","erişte","noodle"],
    "Mutfak Banyo Temizlik": ["çamaşır suyu","yüzey temizleyici","banyo temizleyici","fayans","duşakabin","mutfak temizleyici","lavabo açıcı","yağ temizleyici","kireç","gider","fırın","ocak","sarı güç"],
    "Saç Bakımı": ["şampuan","saç kremi","saç maskesi","saç yağı","dökülme","saç","keratin","tarak"],
    "Sıvı Yağlar": ["zeytinyağı","ayçiçek yağı","mısır yağı"],
    "Toz Şeker": ["toz şekeri","pudra şekeri"],
    "Tıraş Ürünleri": ["tıraş köpüğü","tıraş bıçağı","tıraş sonrası losyon","tıraş"],
    "Unlu Mamul": ["poğaça","simit","börek","çörek","kömbe","kurabiye","katmer"],
    "Çamaşır Deterjanı": ["toz deterjan","sıvı deterjan","kapsül deterjan"],
    "Çamaşır Yıkama Ürünleri": ["leke çıkarıcı","renk koruyucu","çamaşır filesi","deterjan"],
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

# --- ROTALAR ---

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/add_to_cart', methods=['POST'])
def add_to_cart_ajax():


    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Sepet oturumunu bul veya oluştur
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
        res = cur.fetchone()

        if res:
            session_id = res[0]
        else:
            cur.execute('INSERT INTO shoppingsession (userid) VALUES (%s) RETURNING id', (session['user_id'],))
            session_id = cur.fetchone()[0]

        # Ürünü ekle (Varsa miktar artır - ON CONFLICT mantığı yoksa manuel kontrol)
        # Basitlik için direkt insert deniyoruz, varsa update mantığı eklenebilir.
        # Senin tablonda UNIQUE constraint yoksa direkt ekler.

        # Önce var mı diye bak
        cur.execute('SELECT id, quantity FROM cartitem WHERE sessionid=%s AND productid=%s', (session_id, product_id))
        existing = cur.fetchone()

        if existing:
            new_qty = existing[1] + quantity
            cur.execute('UPDATE cartitem SET quantity=%s WHERE id=%s', (new_qty, existing[0]))
        else:
            cur.execute('INSERT INTO cartitem (sessionid, productid, quantity) VALUES (%s, %s, %s)', (session_id, product_id, quantity))

        conn.commit()

        # --- DÜZELTME: Güncel sepet sayısını hesapla ve döndür ---
        new_cart_count = get_cart_count(session['user_id'])
        return jsonify({'status': 'success', 'cart_count': new_cart_count})

    except Exception as e:
        conn.rollback()
        print(f"Sepet Hatası: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT id, password, name FROM "user" WHERE email = %s', (email,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user:
                stored_password_hash = user[1]
                if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                    session['user_id'] = user[0]
                    session['name'] = user[2]
                    return jsonify({'status': 'success', 'message': 'Giriş başarılı!'})
                return jsonify({'status': 'error', 'message': 'E-posta veya şifre hatalı.'})
            return jsonify({'status': 'error', 'message': 'E-posta veya şifre hatalı.'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Sunucu hatası.'})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')
        street = data.get('street')
        city = data.get('city')
        zipcode = data.get('zipcode')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO "user" (name, email, password, phone) VALUES (%s, %s, %s, %s) RETURNING id',
                (name, email, hashed_password, phone)
            )
            new_user_id = cur.fetchone()[0]
            if street or city or zipcode:
                cur.execute(
                    'INSERT INTO address (userid, street, city, zipcode) VALUES (%s, %s, %s, %s)',
                    (new_user_id, street, city, zipcode)
                )
            conn.commit()
            cur.close()
            return jsonify({'status': 'success', 'message': 'Kayıt başarılı!'})
        except psycopg2.IntegrityError:
            if conn: conn.rollback()
            return jsonify({'status': 'error', 'message': 'Bu e-posta zaten kayıtlı.'})
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'status': 'error', 'message': f'Hata: {str(e)}'})
        finally:
            if conn: conn.close()
    return render_template('register.html')


# MARKET (DÜZELTİLDİ: current_page Hatası Giderildi)
@app.route('/market')
def market():
    # Sayfa ve Arama parametrelerini al
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')

    conn = get_db_connection()
    cur = conn.cursor()

    offset = (page - 1) * 6

    if search_query:
        # Arama Yapılıyorsa
        cur.execute("SELECT * FROM view_product_summary WHERE name ILIKE %s LIMIT 6 OFFSET %s", (f"%{search_query}%", offset))
    else:
        # Normal Listeleme
        cur.execute("SELECT * FROM view_product_summary ORDER BY id LIMIT 6 OFFSET %s", (offset,))

    products = cur.fetchall()

    # --- DÜZELTME: Sepet sayısını al ---
    cart_count = 0
    if 'user_id' in session:
        cart_count = get_cart_count(session['user_id'])

    conn.close()

    # HTML'e GEREKLİ TÜM DEĞİŞKENLERİ GÖNDERİYORUZ
    return render_template('market.html', products=products, current_page=page, search_query=search_query, cart_count=cart_count)

# SEPETİM
# --- MEVCUT 'cart' ROTASINI BUNUNLA DEĞİŞTİR ---
# (Değişiklik sebebi: SQL sorgusuna 'p.id' eklendi, böylece butonlar hangi ürünü güncelleyeceğini bilir)
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    # Sepeti Bul
    cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
    session_row = cur.fetchone()

    cart_items = []
    total_amount = 0
    # --- DÜZELTME: Sepet sayısını al ---
    cart_count = get_cart_count(session['user_id'])

    if session_row:
        session_id = session_row[0]
        # p.id EKLENDİ (En sona)
        cur.execute("""
                    SELECT p.name, p.price, ci.quantity, (p.price * ci.quantity) as total, p.image_url, p.id
                    FROM cartitem ci
                             JOIN product p ON ci.productid = p.id
                    WHERE ci.sessionid = %s
                    ORDER BY p.name
                    """, (session_id,))
        cart_items = cur.fetchall()

        if cart_items:
            total_amount = sum(item[3] for item in cart_items)

    conn.close()
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount, cart_count=cart_count)

# --- YENİ EKLENECEK ROTA: SEPET GÜNCELLEME (+ / -) ---
# (Bu kodu dosyanın en altına, if __name__ öncesine ekle)
@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapın'})

    data = request.get_json()
    product_id = data.get('product_id')
    action = data.get('action') # 'increase' veya 'decrease'

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Session ID bul
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
        res = cur.fetchone()
        if not res: return jsonify({'status': 'error'})
        session_id = res[0]

        # Mevcut adeti bul
        cur.execute('SELECT quantity FROM cartitem WHERE sessionid=%s AND productid=%s', (session_id, product_id))
        item = cur.fetchone()

        if item:
            current_qty = item[0]
            new_qty = current_qty

            if action == 'increase':
                new_qty += 1
            elif action == 'decrease':
                new_qty -= 1

            if new_qty > 0:
                cur.execute('UPDATE cartitem SET quantity=%s WHERE sessionid=%s AND productid=%s', (new_qty, session_id, product_id))
            else:
                # Adet 0 olursa ürünü sepetten sil
                cur.execute('DELETE FROM cartitem WHERE sessionid=%s AND productid=%s', (session_id, product_id))

            conn.commit()

            # --- DÜZELTME: Güncel sayıyı döndür ---
            new_cart_count = get_cart_count(session['user_id'])
            return jsonify({'status': 'success', 'cart_count': new_cart_count})

        return jsonify({'status': 'error', 'message': 'Ürün bulunamadı'})

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()
# HESABIM (DÜZELTİLDİ: Adres ve Sesli Asistan Eklendi)
# --- HESABIM ROTASI (GÜNCELLENMİŞ: E-posta ve Şifre Değişimi Ekli) ---
@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    message = None
    message_type = "success" # veya 'error'

    # GÜNCELLEME İSTEĞİ
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        new_password = request.form.get('new_password') # Yeni şifre alanı

        street = request.form.get('street')
        city = request.form.get('city')
        zipcode = request.form.get('zipcode')

        try:
            # 1. Temel Bilgileri Güncelle (Ad, Tel, Email)
            # Not: Email unique (eşsiz) olmalı, hata verirse except bloğu yakalar
            cur.execute('UPDATE "user" SET name=%s, phone=%s, email=%s WHERE id=%s',
                        (name, phone, email, session['user_id']))

            # 2. Şifre Değişimi İstenmişse
            if new_password and new_password.strip():
                # Şifreyi hashle
                hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute('UPDATE "user" SET password=%s WHERE id=%s', (hashed_pw, session['user_id']))

            # 3. Adres Bilgilerini Güncelle
            cur.execute('SELECT id FROM address WHERE userid=%s', (session['user_id'],))
            addr = cur.fetchone()

            if addr:
                cur.execute('UPDATE address SET street=%s, city=%s, zipcode=%s WHERE userid=%s',
                            (street, city, zipcode, session['user_id']))
            else:
                cur.execute('INSERT INTO address (userid, street, city, zipcode) VALUES (%s, %s, %s, %s)',
                            (session['user_id'], street, city, zipcode))

            conn.commit()
            message = "Bilgileriniz başarıyla güncellendi."

        except psycopg2.IntegrityError:
            conn.rollback()
            message = "Bu e-posta adresi başka bir kullanıcı tarafından kullanılıyor."
            message_type = "error"
        except Exception as e:
            conn.rollback()
            message = f"Hata oluştu: {str(e)}"
            message_type = "error"

    # BİLGİLERİ ÇEK (Sayfa Yüklenirken)
    cur.execute('SELECT name, email, phone FROM "user" WHERE id = %s', (session['user_id'],))
    user_info = cur.fetchone()

    cur.execute('SELECT street, city, zipcode FROM address WHERE userid = %s', (session['user_id'],))
    address_info = cur.fetchone()

    cur.execute('SELECT id, totalamount, orderdate, status FROM "Order" WHERE userid = %s ORDER BY orderdate DESC', (session['user_id'],))
    orders = cur.fetchall()

    conn.close()

    addr_data = address_info if address_info else ("", "", "")

    return render_template('account.html', user=user_info, address=addr_data, orders=orders, msg=message, msg_type=message_type)

@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    voice_query = data.get('query', '').lower()
    offset = data.get('offset', 0)

    # "En ucuz" filtresi var mı?
    is_cheapest = "en ucuz" in voice_query or "uygun" in voice_query

    # Temiz sorgu (filtre kelimelerini atalım)
    clean_query = voice_query.replace("en ucuz", "").replace("uygun", "").strip()

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        products_list = []
        found_title = None

        limit_clause = f" LIMIT 6 OFFSET {offset}"
        order_clause = " ORDER BY price ASC" if is_cheapest else " ORDER BY id"

        # --- STRATEJİ 1: DİREKT ÜRÜN İSMİ ARAMA (ÖNCELİKLİ) ---
        # "Yumurta" dediyse, içinde "yumurta" geçen ürünleri getir.
        # ILIKE: Büyük/küçük harf duyarsız arama
        sql_product = f"SELECT id, name, price FROM product WHERE name ILIKE %s {order_clause} {limit_clause}"
        cur.execute(sql_product, (f"%{clean_query}%",))
        rows = cur.fetchall()

        if rows:
            # Eğer ürün bulunduysa bunları kullan
            found_title = f"'{clean_query}' araması"
            for row in rows:
                products_list.append({'id': row[0], 'name': row[1], 'price': float(row[2])})

        # --- STRATEJİ 2: KATEGORİ ARAMA (YEDEK) ---
        # Eğer ürün isminden bir şey çıkmadıysa (örn: "kahvaltılık" dedi), kategoriye bak.
        else:
            target_category = None
            # Sözlükten kategori tahmini
            for kategori_adi, anahtar_kelimeler in kategoriler.items():
                for kelime in anahtar_kelimeler:
                    if kelime in voice_query:
                        target_category = kategori_adi
                        break
                if target_category: break

            if target_category:
                # Veritabanında kategori ID'sini bul
                cur.execute("SELECT id, name FROM category WHERE name ILIKE %s", (f"%{target_category}%",))
                cat_row = cur.fetchone()

                if cat_row:
                    cat_id = cat_row[0]
                    found_title = cat_row[1] # Kategori adı (örn: Kahvaltılık)

                    # O kategorideki ürünleri getir
                    sql_cat = f"SELECT id, name, price FROM product WHERE categoryid = %s {order_clause} {limit_clause}"
                    cur.execute(sql_cat, (cat_id,))
                    rows = cur.fetchall()
                    for row in rows:
                        products_list.append({'id': row[0], 'name': row[1], 'price': float(row[2])})

        # --- SONUÇLARI DÖNDÜR ---
        if products_list:
            final_products = []
            for p in products_list:
                # Resim üretme
                fake_image_url = f"https://placehold.co/400x300/e6e6e6/000000?text={p['name'].replace(' ', '+')}"

                final_products.append({
                    'id': p['id'],
                    'name': p['name'],
                    'price': p['price'],
                    'image': fake_image_url
                })

            has_more = len(final_products) == 6
            msg = f"{found_title} bulundu."

            return jsonify({
                'status': 'success',
                'products': final_products,
                'category_name': found_title,
                'has_more': has_more,
                'message_text': msg
            })
        else:
            return jsonify({'status': 'empty', 'message': 'Ürün bulunamadı.'})

    except Exception as e:
        print(f"Arama Hatası: {e}")
        return jsonify({'status': 'error', 'message': 'Veritabanı hatası.'})
    finally:
        if conn: conn.close()


@app.route('/remove_cart_item', methods=['POST'])
def remove_cart_item():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login gerekli"})

    data = request.get_json()
    product_id = data.get("product_id")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM shoppingsession WHERE userid=%s", (session['user_id'],))
        sid = cur.fetchone()
        if sid:
            cur.execute("DELETE FROM cartitem WHERE productid=%s AND sessionid=%s", (product_id, sid[0]))
            conn.commit()
            # --- DÜZELTME: Güncel sayıyı döndür ---
            new_cart_count = get_cart_count(session['user_id'])
            return jsonify({"status": "success", "cart_count": new_cart_count})
    except:
        return jsonify({"status": "error"})
    finally:
        conn.close()

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login gerekli"})

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM shoppingsession WHERE userid=%s", (session['user_id'],))
        sid = cur.fetchone()
        if sid:
            cur.execute("DELETE FROM cartitem WHERE sessionid=%s", (sid[0],))
            conn.commit()
            return jsonify({"status": "success", "cart_count": 0}) # Sepet sıfırlandı
    except:
        return jsonify({"status": "error"})
    finally:
        conn.close()

# --- SES TANIMA (HIZLI & GECİKMESİZ) ---
@app.route('/dinle', methods=['POST'])
def dinle():
    global CURRENT_STATE, LAST_CATEGORY
    r = sr.Recognizer()
    command = ""
    status = "error"
    message = "Ses algılanamadı."

    try:
        # with sr.Microphone() kullanımı bazen sunucu tarafında donanım erişim hatası verebilir.
        # Eğer bu kod sunucuda çalışıyorsa hata verir, lokalde çalışıyorsa çalışır.
        # Try bloğu ile güvene alıyoruz.
        with sr.Microphone() as source:
            r.energy_threshold = 400
            r.dynamic_energy_threshold = False
            r.pause_threshold = 0.8
            print("🎤 Python: Dinliyorum (Gecikmesiz)...")

            # Timeout süresini kısalttık, çakışmayı önlemek için
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            command = r.recognize_google(audio, language='tr-tr').lower()
            print(f"🗣 Algılanan: {command}")
            status = "success"
            message = f"Algılanan: {command}"

            # --- KOMUT İŞLEME MANTIĞI ---
            if CURRENT_STATE == "MAIN_MENU":
                if "ürün" in command or "al" in command:
                    CURRENT_STATE = "SEARCH"
                    return jsonify({"status": "success", "state": "SEARCH", "message": "Ne almak istiyorsunuz?"})
                if "sepet" in command:
                    return jsonify({"status":"success", "state":"OPEN_CART", "message":"Sepetinizi açıyorum."})
                if "hesabım" in command:
                    return jsonify({"status": "success", "state": "ACCOUNT", "message": "Hesabınıza bakılıyor."})

            if CURRENT_STATE == "SEARCH":
                found_category = None
                for kategori, kelimeler in kategoriler.items():
                    for k in kelimeler:
                        if k in command:
                            found_category = kategori
                            break
                    if found_category: break

                if found_category:
                    LAST_CATEGORY = found_category
                    CURRENT_STATE = "CATEGORY_CONFIRM"
                    return jsonify({"status": "success", "state": "CATEGORY_CONFIRM", "category": found_category, "message": f"{found_category} kategorisi bulundu. Listeleyeyim mi?"})

                # Eğer kategori bulunamadıysa ama komut varsa SEARCH'e devam et
                return jsonify({"status": "success", "state": "SEARCH", "message": "Uygun kategori bulamadım."})

            if CURRENT_STATE == "CATEGORY_CONFIRM":
                if "hayır" in command:
                    CURRENT_STATE = "MAIN_MENU"
                    return jsonify({"status": "success", "state": "MAIN_MENU", "message": "İptal edildi."})
                if "evet" in command or "listele" in command:
                    CURRENT_STATE = "LIST_PRODUCTS"
                    return jsonify({"status": "success", "state": "LIST_PRODUCTS", "query": LAST_CATEGORY})

    except sr.WaitTimeoutError:
        message = "Süre doldu."
    except sr.UnknownValueError:
        message = "Anlayamadım."
    except Exception as e:
        # En kötü ihtimalle -1 hatasını önlemek için genel exception
        print(f"KRİTİK HATA: {e}")
        message = "Sistem hatası."

    return jsonify({'status': status, 'command': command, 'message': message})

if __name__ == '__main__':
    app.run(debug=True)