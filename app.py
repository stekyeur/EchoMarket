from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import speech_recognition as sr
import psycopg2
from psycopg2 import pool
import bcrypt
from datetime import datetime
from config import DB_CONFIG

CURRENT_STATE = "MAIN_MENU"
LAST_CATEGORY = None
app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar_sabit_kalsin"

# --- ORTAK TEMİZLEME FONKSİYONU (GÜNCELLENDİ) ---
def clean_search_text(text):
    if not text: return ""
    text = text.lower()

    # 1. Konuşma Dolgu Kelimeleri
    filler_phrases = [
        "satın almak istiyorum", "almak istiyorum", "istiyorum",
        "arıyorum", "bul", "getir", "göster", "listele",
        "bana", "satın al", "alacağım", "lazım", "var mı",
        "bulsana", "ekle", "sipariş ver", "bak", "bakar mısın"
    ]
    for phrase in filler_phrases:
        text = text.replace(phrase, "")

    # 2. Filtre Kelimeleri (Pahalı filtresi eklendi)
    filter_words = [
        "en ucuz", "uygun fiyatlı", "uygun", "en düşük fiyatlı",
        "en pahalı", "en yüksek fiyatlı", "pahalı",
        "en iyi", "en yüksek puan", "yüksek puan","en yüksek puanlı",
        "önerilen", "kaliteli"
    ]
    for f in filter_words:
        text = text.replace(f, "")

    return " ".join(text.split())

# --- 1. BAĞLANTI HAVUZU (HIZ İÇİN) ---
try:
    postgreSQL_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1, maxconn=20, **DB_CONFIG, sslmode='require'
    )
    print("✅ Veritabanı Bağlantı Havuzu Başarıyla Oluşturuldu.")
except Exception as e:
    print(f"❌ Havuz Oluşturma Hatası: {e}")

# Havuzdan bağlantı al
def get_db_connection():
    return postgreSQL_pool.getconn()

# Bağlantıyı havuza geri bırak (Kapatma, iade et)
def close_db_connection(conn):
    if conn:
        postgreSQL_pool.putconn(conn)

# --- YARDIMCI: Sepet Sayısı ---
def get_cart_count(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (user_id,))
        session_row = cur.fetchone()
        if session_row:
            cur.execute('SELECT SUM(quantity) FROM cartitem WHERE sessionid = %s', (session_row[0],))
            res = cur.fetchone()
            return int(res[0]) if res and res[0] else 0
        return 0
    except: return 0
    finally: close_db_connection(conn)

# Kategori Listesi (Sesli komut için)
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

# --- LOGOUT (ÇIKIŞ YAP) ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT id, password, name FROM "user" WHERE email = %s', (data['email'],))
            user = cur.fetchone()
            
            if user and bcrypt.checkpw(data['password'].encode('utf-8'), user[1].encode('utf-8')):
                session['user_id'] = user[0]
                session['name'] = user[2]
                return jsonify({'status': 'success', 'message': 'Giriş başarılı!'})
            return jsonify({'status': 'error', 'message': 'Hatalı giriş.'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Sunucu hatası.'})
        finally:
            close_db_connection(conn)
    return render_template('login.html')

# --- REGISTER (KAYIT OL) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            hashed_pw = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cur.execute(
                'INSERT INTO "user" (name, email, password, phone) VALUES (%s, %s, %s, %s) RETURNING id',
                (data.get('full_name'), data.get('email'), hashed_pw, data.get('phone'))
            )
            new_uid = cur.fetchone()[0]
            
            if data.get('street') or data.get('city') or data.get('zipcode'):
                cur.execute('INSERT INTO address (userid, street, city, zipcode) VALUES (%s, %s, %s, %s)',
                           (new_uid, data.get('street'), data.get('city'), data.get('zipcode')))
            
            conn.commit()
            return jsonify({'status': 'success'})
        except psycopg2.IntegrityError:
            if conn: conn.rollback()
            return jsonify({'status': 'error', 'message': 'Bu e-posta kayıtlı.'})
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)})
        finally:
            close_db_connection(conn)
    return render_template('register.html')

@app.route('/market')
def market():
    page = request.args.get('page', 1, type=int)
    raw_query = request.args.get('q', '').lower()

    cart_count = 0
    if 'user_id' in session:
        cart_count = get_cart_count(session['user_id'])

    # Temizlik
    clean_query = clean_search_text(raw_query)

    # Filtre Tespiti
    is_cheapest = "en ucuz" in raw_query or "uygun" in raw_query or "en düşük fiyat" in raw_query
    is_expensive = "en pahalı" in raw_query or "en yüksek fiyat" in raw_query # YENİ EKLENDİ
    is_top_rated = "en iyi" in raw_query or "yüksek puan" in raw_query

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        offset = (page - 1) * 4

        base_query = """
                     SELECT v.id, v.name, v.price, v.image_url, v.category_name, COALESCE(AVG(pr.rating), 0) as avg_rating
                     FROM view_product_summary v
                              LEFT JOIN productrating pr ON v.id = pr.productid \
                     """
        group = " GROUP BY v.id, v.name, v.price, v.image_url, v.category_name"

        # SIRALAMA MANTIĞI (GÜNCELLENDİ)
        if is_cheapest: order = " ORDER BY v.price ASC"
        elif is_expensive: order = " ORDER BY v.price DESC" # YENİ: Pahalıdan ucuza
        elif is_top_rated: order = " ORDER BY avg_rating DESC NULLS LAST"
        else: order = " ORDER BY v.id"

        limits = f" LIMIT 4 OFFSET {offset}"

        rows = []

        pattern = rf"\m{clean_query}\M"
        cur.execute(
    base_query + " WHERE v.name ~* %s" + group + order + limits,
    (pattern,)
)
        rows = cur.fetchall()

# 2. Kategoriyle Ara
        if not rows and clean_query:
            cur.execute(base_query + " WHERE v.category_name ILIKE %s" + group + order + limits, (f"%{clean_query}%",))
            rows = cur.fetchall()

        # 3. Sadece Filtre Varsa (Örn: "En pahalıları getir")
        if not rows and not clean_query and (is_cheapest or is_top_rated or is_expensive):
            cur.execute(base_query + group + order + limits)
            rows = cur.fetchall()

        products = []
        for row in rows:
            products.append({
                'id': row[0], 'name': row[1], 'price': float(row[2]),
                'image': row[3], 'category': row[4],
                'rating': float(round(row[5], 1))
            })

        # Eğer arama yoksa ve ürün yoksa hoşgeldin modu
        is_welcome = (not raw_query) and (not products)

        return render_template('market.html', products=products, current_page=page, search_query=raw_query, cart_count=cart_count, welcome_mode=is_welcome)
    finally:
        close_db_connection(conn)

@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    voice_query = data.get('query', '').lower()
    offset = data.get('offset', 0)

    # Filtre Tespiti
    is_cheapest = "en ucuz" in voice_query or "uygun" in voice_query or "en düşük fiyat" in voice_query
    is_expensive = "en pahalı" in voice_query or "en yüksek fiyat" in voice_query
    is_top_rated = "en iyi" in voice_query or "yüksek puan" in voice_query

    # Temizlik
    clean_query = clean_search_text(voice_query)

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        products_list = []
        found_title = None
        rows = None  # güvenli olsun diye baştan tanımlıyoruz

        base_sql = """
                   SELECT v.id, v.name, v.price, v.image_url, v.category_name,
                          COALESCE(AVG(pr.rating), 0) as avg_rating
                   FROM view_product_summary v
                            LEFT JOIN productrating pr ON v.id = pr.productid \
                   """

        group = " GROUP BY v.id, v.name, v.price, v.image_url, v.category_name"

        # SIRALAMA
        if is_cheapest:
            order = " ORDER BY v.price ASC"
        elif is_expensive:
            order = " ORDER BY v.price DESC"
        elif is_top_rated:
            order = " ORDER BY avg_rating DESC NULLS LAST"
        else:
            order = " ORDER BY v.id"

        limits = f" LIMIT 4 OFFSET {offset}"

        # 1️⃣ İSİM ARAMA (REGEX + KELİME SINIRI)
        if clean_query:
            pattern = rf"\m{clean_query}\M"
            cur.execute(
                base_sql + " WHERE v.name ~* %s" + group + order + limits,
                (pattern,)
            )
            rows = cur.fetchall()
            if rows:
                found_title = f"'{clean_query}' araması"

        # 2️⃣ KATEGORİ ARAMA
        if (not rows or not found_title) and clean_query:
            cur.execute(
                base_sql + " WHERE v.category_name ILIKE %s" + group + order + limits,
                (f"%{clean_query}%",)
            )
            rows = cur.fetchall()
            if rows:
                found_title = f"'{clean_query}' kategorisi"

        # 3️⃣ SADECE FİLTRE (Ürün adı yoksa)
        if not rows and not clean_query:
            if is_expensive or is_cheapest or is_top_rated:
                cur.execute(base_sql + group + order + limits)
                rows = cur.fetchall()
                if is_expensive:
                    found_title = "En yüksek fiyatlı ürünler"
                elif is_cheapest:
                    found_title = "En uygun fiyatlı ürünler"
                elif is_top_rated:
                    found_title = "En yüksek puanlı ürünler"

        # SONUÇLARI DÖN
        if rows:
            for row in rows:
                img = row[3] if row[3] else f"https://placehold.co/400?text={row[1]}"
                products_list.append({
                    'id': row[0],
                    'name': row[1],
                    'price': float(row[2]),
                    'image': img,
                    'category': row[4],
                    'rating': float(round(row[5], 1))
                })

            msg = f"{found_title} bulundu." if found_title else "Sonuçlar bulundu."
            return jsonify({
                'status': 'success',
                'products': products_list,
                'message_text': msg
            })

        return jsonify({'status': 'empty', 'message': 'Ürün bulunamadı.'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

    finally:
        close_db_connection(conn)

# --- CART (SEPET) ---
@app.route('/cart')
def cart():
    if 'user_id' not in session: return redirect('/login')
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
        s_row = cur.fetchone()
        
        cart_items = []
        total = 0
        if s_row:
            cur.execute("""
                SELECT p.name, p.price, ci.quantity, (p.price * ci.quantity), p.image_url, p.id
                FROM cartitem ci JOIN product p ON ci.productid = p.id
                WHERE ci.sessionid = %s ORDER BY p.name
            """, (s_row[0],))
            cart_items = cur.fetchall()
            if cart_items: total = sum(i[3] for i in cart_items)
            
        cnt = get_cart_count(session['user_id'])
        return render_template('cart.html', cart_items=cart_items, total_amount=total, cart_count=cnt)
    finally:
        close_db_connection(conn)

# --- ADD TO CART ---
# --- SEPETE EKLEME (DÜZELTİLMİŞ VERSİYON) ---
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart_ajax():
    if 'user_id' not in session: 
        return jsonify({'status': 'error', 'message': 'Giriş yapın'})
    
    data = request.get_json()
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Kullanıcının açık bir sepet oturumu var mı kontrol et
        cur.execute('SELECT id FROM shoppingsession WHERE userid=%s', (session['user_id'],))
        row = cur.fetchone()
        
        sid = None
        if row:
            # Varsa ID'yi al (Eski kullanıcılar buraya girer, sorun çıkmaz)
            sid = row[0]
        else:
            # Yoksa YENİ OLUŞTUR (Yeni kullanıcılar buraya girer)
            # HATA BURADAYDI: execute().fetchone() zincirleme yapılamaz. Ayırdık.
            cur.execute('INSERT INTO shoppingsession (userid) VALUES (%s) RETURNING id', (session['user_id'],))
            sid = cur.fetchone()[0]
        
        # 2. Ürünü sepete ekle (Varsa güncelle, yoksa ekle mantığı)
        # Önce bu ürün sepette var mı diye bakıyoruz
        cur.execute('SELECT id, quantity FROM cartitem WHERE sessionid=%s AND productid=%s', (sid, data['product_id']))
        item = cur.fetchone()

        if item:
            # Varsa miktarını 1 artır
            new_qty = item[1] + 1
            cur.execute('UPDATE cartitem SET quantity=%s WHERE id=%s', (new_qty, item[0]))
        else:
            # Yoksa yeni satır ekle
            cur.execute('INSERT INTO cartitem (sessionid, productid, quantity) VALUES (%s, %s, 1)', (sid, data['product_id']))
            
        conn.commit()
        cnt = get_cart_count(session['user_id'])
        return jsonify({'status': 'success', 'cart_count': cnt})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Sepet Hatası: {e}") # Konsola hatayı yazdırır, sorunu görmeni sağlar
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        close_db_connection(conn)

# --- UPDATE CART (+/-) ---
@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session: return jsonify({'status': 'error'})
    data = request.get_json()
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT id FROM shoppingsession WHERE userid=%s', (session['user_id'],))
        s_row = cur.fetchone()
        if not s_row: return jsonify({'status': 'error'})
        
        cur.execute('SELECT quantity FROM cartitem WHERE sessionid=%s AND productid=%s', (s_row[0], data['product_id']))
        item = cur.fetchone()
        
        if item:
            new_qty = item[0] + 1 if data['action'] == 'increase' else item[0] - 1
            if new_qty > 0:
                cur.execute('UPDATE cartitem SET quantity=%s WHERE sessionid=%s AND productid=%s', (new_qty, s_row[0], data['product_id']))
            else:
                cur.execute('DELETE FROM cartitem WHERE sessionid=%s AND productid=%s', (s_row[0], data['product_id']))
            conn.commit()
            return jsonify({'status': 'success', 'cart_count': get_cart_count(session['user_id'])})
        return jsonify({'status': 'error'})
    except:
        if conn: conn.rollback()
        return jsonify({'status': 'error'})
    finally:
        close_db_connection(conn)

# --- ACCOUNT (HESABIM) ---
@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session: return redirect('/login')
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        msg = None
        m_type = "success"

        if request.method == 'POST':
            try:
                cur.execute('UPDATE "user" SET name=%s, phone=%s, email=%s WHERE id=%s',
                           (request.form.get('name'), request.form.get('phone'), request.form.get('email'), session['user_id']))
                
                if request.form.get('new_password'):
                    hashed = bcrypt.hashpw(request.form.get('new_password').encode(), bcrypt.gensalt()).decode()
                    cur.execute('UPDATE "user" SET password=%s WHERE id=%s', (hashed, session['user_id']))
                
                cur.execute('SELECT id FROM address WHERE userid=%s', (session['user_id'],))
                if cur.fetchone():
                    cur.execute('UPDATE address SET street=%s, city=%s, zipcode=%s WHERE userid=%s',
                               (request.form.get('street'), request.form.get('city'), request.form.get('zipcode'), session['user_id']))
                else:
                    cur.execute('INSERT INTO address (userid, street, city, zipcode) VALUES (%s, %s, %s, %s)',
                               (session['user_id'], request.form.get('street'), request.form.get('city'), request.form.get('zipcode')))
                
                conn.commit()
                msg = "Bilgiler güncellendi."
            except psycopg2.IntegrityError:
                conn.rollback(); msg = "E-posta kullanımda."; m_type = "error"
            except Exception as e:
                conn.rollback(); msg = str(e); m_type = "error"

        # Bilgileri Çek
        cur.execute('SELECT name, email, phone FROM "user" WHERE id=%s', (session['user_id'],))
        u_info = cur.fetchone()
        cur.execute('SELECT street, city, zipcode FROM address WHERE userid=%s', (session['user_id'],))
        addr = cur.fetchone()
        cur.execute('SELECT id, totalamount, orderdate, status FROM "Order" WHERE userid=%s ORDER BY orderdate DESC', (session['user_id'],))
        orders = cur.fetchall()
        
        return render_template('account.html', user=u_info, address=addr if addr else ("","",""), orders=orders, msg=msg, msg_type=m_type, cart_count=get_cart_count(session['user_id']))
    finally:
        close_db_connection(conn)

# --- CHECKOUT (SİPARİŞ VER) ---
@app.route('/checkout', methods=['POST'])
def checkout_action():
    if 'user_id' not in session: return jsonify({'status': 'error', 'message': 'Giriş yapın'})
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT id FROM shoppingsession WHERE userid=%s', (session['user_id'],))
        row = cur.fetchone()
        if not row: return jsonify({'status': 'error', 'message': 'Sepet boş'})
        sid = row[0]
        
        cur.execute('SELECT ci.productid, ci.quantity, p.price FROM cartitem ci JOIN product p ON ci.productid=p.id WHERE ci.sessionid=%s', (sid,))
        items = cur.fetchall()
        if not items: return jsonify({'status': 'error', 'message': 'Sepet boş'})
        
        total = sum(i[1]*i[2] for i in items)
        
        cur.execute('INSERT INTO "Order" (userid, orderdate, totalamount, status) VALUES (%s, %s, %s, %s) RETURNING id',
                   (session['user_id'], datetime.now().date(), total, 'Hazırlanıyor'))
        oid = cur.fetchone()[0]
        
        for i in items:
            cur.execute('INSERT INTO orderitem (orderid, productid, quantity, price) VALUES (%s, %s, %s, %s)', (oid, i[0], i[1], i[2]))
            
        cur.execute('DELETE FROM cartitem WHERE sessionid=%s', (sid,))
        conn.commit()
        return jsonify({'status': 'success', 'order_id': oid})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        close_db_connection(conn)
@app.route('/remove_cart_item', methods=['POST'])
def remove_cart_item():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapın'})

    product_id = request.form.get("product_id") or request.json.get("product_id")

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT id FROM shoppingsession WHERE userid=%s',
                    (session['user_id'],))
        s_row = cur.fetchone()
        if not s_row:
            return jsonify({'status': 'error', 'message': 'Sepet bulunamadı'})

        cur.execute('DELETE FROM cartitem WHERE sessionid=%s AND productid=%s',
                    (s_row[0], product_id))

        conn.commit()
        return jsonify({'status': 'success'})

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        close_db_connection(conn)

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapın'})

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT id FROM shoppingsession WHERE userid=%s',
                    (session['user_id'],))
        s_row = cur.fetchone()
        if not s_row:
            return jsonify({'status': 'success'})

        cur.execute('DELETE FROM cartitem WHERE sessionid=%s', (s_row[0],))
        conn.commit()

        return jsonify({'status': 'success'})

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        close_db_connection(conn)

# --- SİPARİŞ BAŞARILI ---
@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    if 'user_id' not in session: return redirect('/login')
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, totalamount, orderdate, status FROM "Order" WHERE id=%s AND userid=%s', (order_id, session['user_id']))
        order = cur.fetchone()
        if not order: return "Sipariş bulunamadı", 404
        
        cur.execute('SELECT p.name, oi.quantity, oi.price, p.image_url FROM orderitem oi JOIN product p ON oi.productid=p.id WHERE oi.orderid=%s', (order_id,))
        items = cur.fetchall()
        
        return render_template('order_success.html', order=order, items=items, cart_count=get_cart_count(session['user_id']))
    finally:
        close_db_connection(conn)

# --- SESLİ KOMUT (DINLE) - SAYFA GEÇİŞ ÖZELLİKLİ ---
@app.route('/dinle', methods=['POST'])
def dinle():
    global CURRENT_STATE, LAST_CATEGORY
    r = sr.Recognizer()
    command = ""
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            r.energy_threshold = 400
            r.dynamic_energy_threshold = False
            r.pause_threshold = 0.8

            print("🎤 Dinliyorum...");
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            command = r.recognize_google(audio, language='tr-tr').lower()

            response = {
                'status': 'success',
                'command': command,
                'message': f"Algılanan: {command}",
                'state': CURRENT_STATE
            }

            # --- 1. SAYFA GEÇİŞ KOMUTLARI (YENİ EKLENDİ) ---
            if "sonraki" in command or "diğer" in command or "hiçbiri" in command or "devam" in command:
                response.update({
                    "action": "next_page",
                    "message": "Diğer ürünler getiriliyor."
                })
                return jsonify(response)

            if command.strip() in ["hiçbiri", "devam"]:
                 response.update({
                     "action": "next_page",
                     "message": "Diğer ürünler getiriliyor."
                 })
                 return jsonify(response)

            # --- 2. GLOBAL YÖNLENDİRMELER ---
            if "çıkış" in command or "oturumu kapat" in command:
                response.update({"action": "redirect", "redirect_url": "/logout", "message": "Çıkış yapılıyor."})
                return jsonify(response)

            if "giriş" in command:
                response.update({"action": "redirect", "redirect_url": "/login", "message": "Giriş ekranına yönlendiriliyorsunuz."})
                return jsonify(response)

            if "kayıt" in command:
                response.update({"action": "redirect", "redirect_url": "/register", "message": "Kayıt ekranına yönlendiriliyorsunuz."})
                return jsonify(response)

            # --- 3. DURUMA GÖRE KOMUTLAR ---
            if CURRENT_STATE == "MAIN_MENU":
                if "sepet" in command:
                    response.update({"state": "OPEN_CART", "action": "redirect", "redirect_url": "/cart"})
                elif "hesabım" in command:
                    response.update({"state": "ACCOUNT", "action": "redirect", "redirect_url": "/account"})
                elif "market" in command:
                    response.update({"state": "MARKET", "action": "redirect", "redirect_url": "/market"})
                elif "ürün" in command or "al" in command:
                    CURRENT_STATE = "SEARCH"
                    response.update({"state": "SEARCH", "message": "Ne almak istersiniz?"})

            elif CURRENT_STATE == "SEARCH":
                cat = next((c for c, w in kategoriler.items() for k in w if k in command), None)
                if cat:
                    LAST_CATEGORY = cat
                    CURRENT_STATE = "CATEGORY_CONFIRM"
                    response.update({"state": "CATEGORY_CONFIRM", "category": cat, "message": f"{cat} bulundu, listeleyeyim mi?"})
                else:
                    response.update({"state": "SEARCH", "message": "Kategori anlaşılamadı, ürün aranıyor..."})

            elif CURRENT_STATE == "CATEGORY_CONFIRM":
                if "evet" in command or "listele" in command:
                    CURRENT_STATE = "LIST_PRODUCTS"
                    response.update({"state": "LIST_PRODUCTS", "query": LAST_CATEGORY})
                else:
                    CURRENT_STATE = "MAIN_MENU"
                    response.update({"state": "MAIN_MENU", "message": "İptal edildi."})

            return jsonify(response)

    except sr.WaitTimeoutError:
        return jsonify({'status': 'error', 'message': "Süre doldu, ses gelmedi."})
    except sr.UnknownValueError:
        return jsonify({'status': 'error', 'message': "Anlaşılamadı."})
    except Exception as e:
        print(f"HATA: {e}")
        return jsonify({'status': 'error', 'message': "Sistem hatası."})

if __name__ == '__main__':
    app.run(debug=True)