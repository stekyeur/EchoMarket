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
    "Kahvaltılık": ["yumurta","peynir","zeytin","reçel","bal","tereyağı","kaşar","salam","sucuk","sosis","ekmek","labne","yoğurt"],
    "Atıştırmalık": ["çıtır çerez","popcorn","kuru yemiş","kraker","cips","atıştırmalık"],
    "Ağız Bakım": ["diş macunu","diş fırçası","gargara"],
    "Banyo Ürünleri": ["duş jeli","şampuan","sabun","lif"],
    "Bulaşık": ["bulaşık deterjanı","sünger","tablet"],
    "İçecek": ["meyve suyu","limonata","soğuk çay","su","kola","gazoz","soda","ayran"],
    "Bakliyat": ["pirinç","bulgur","mercimek","nohut","fasulye","makarna"],
    "Temizlik": ["çamaşır suyu","yüzey temizleyici","deterjan","yumuşatıcı"],
    "Yağ": ["zeytinyağı","ayçiçek yağı","tereyağı"],
    "Unlu Mamul": ["un","maya","kabartma tozu","vanilya","simit","poğaça"],
    "Şekerleme": ["çikolata","gofret","şeker"]
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

# --- MARKET (RATING + POOL + VIEW) ---
# --- MARKET ROTASI (GÜNCELLENDİ: Başlangıçta Ürün Listelemez) ---
@app.route('/market')
def market():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    cart_count = 0
    if 'user_id' in session:
        cart_count = get_cart_count(session['user_id'])

    # EĞER ARAMA SORGUSU YOKSA -> ÜRÜN GETİRME, SADECE KARŞILAMA YAP
    if not search_query:
        return render_template('market.html', products=[], current_page=page, search_query="", cart_count=cart_count, welcome_mode=True)

    # ARAMA VARSA -> VERİTABANINDAN ÜRÜNLERİ ÇEK
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        offset = (page - 1) * 6

        base_query = """
            SELECT v.id, v.name, v.price, v.image_url, v.category_name, COALESCE(AVG(pr.rating), 0) as avg_rating
            FROM view_product_summary v
            LEFT JOIN productrating pr ON v.id = pr.productid
        """
        group = " GROUP BY v.id, v.name, v.price, v.image_url, v.category_name"
        limits = f" ORDER BY v.id LIMIT 6 OFFSET {offset}"

        # Arama sorgusuna göre filtrele
        cur.execute(base_query + " WHERE v.name ILIKE %s" + group + limits, (f"%{search_query}%",))
        
        rows = cur.fetchall()
        products = []
        for row in rows:
            products.append({
                'id': row[0], 'name': row[1], 'price': float(row[2]),
                'image': row[3], 'category': row[4],
                'rating': float(round(row[5], 1))
            })

        return render_template('market.html', products=products, current_page=page, search_query=search_query, cart_count=cart_count, welcome_mode=False)
    finally:
        close_db_connection(conn)

# --- SEARCH (RATING + POOL + VIEW) ---
# --- ARAMA ROTASI (GÜNCELLENDİ: En Yüksek Puan Eklendi) ---
# --- ARAMA ROTASI (DÜZELTİLDİ: Boşluk Temizleme Eklendi) ---
@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    voice_query = data.get('query', '').lower()
    offset = data.get('offset', 0)
    
    # 1. Filtre Kelimelerini Tespit Et
    is_cheapest = "en ucuz" in voice_query or "uygun" in voice_query
    is_top_rated = "en iyi" in voice_query or "yüksek puan" in voice_query or "en yüksek puan" in voice_query

    # 2. Kelime Temizliği (Daha Güçlü Temizlik)
    # Filtre kelimelerini kaldır
    temp_query = voice_query.replace("en ucuz", "").replace("uygun", "") \
                            .replace("en yüksek puan", "").replace("en iyi", "") \
                            .replace("yüksek puan", "").replace("önerilen", "")
    
    # Arada kalan fazla boşlukları silip tek boşluğa indir (Örn: "deterjan   " -> "deterjan")
    clean_query = " ".join(temp_query.split())
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        products_list = []
        found_title = None
        
        # Temel Sorgu
        base_sql = """
            SELECT v.id, v.name, v.price, v.image_url, v.category_name, COALESCE(AVG(pr.rating), 0) as avg_rating
            FROM view_product_summary v
            LEFT JOIN productrating pr ON v.id = pr.productid
        """
        group = " GROUP BY v.id, v.name, v.price, v.image_url, v.category_name"
        
        # SIRALAMA MANTIĞI
        if is_cheapest:
            order = " ORDER BY v.price ASC"
        elif is_top_rated:
            order = " ORDER BY avg_rating DESC NULLS LAST"
        else:
            order = " ORDER BY v.id"
            
        limits = f" LIMIT 6 OFFSET {offset}"

        # 1. İsim Arama (clean_query boşsa arama yapma)
        if clean_query:
            cur.execute(base_sql + " WHERE v.name ILIKE %s" + group + order + limits, (f"%{clean_query}%",))
            rows = cur.fetchall()
            if rows: found_title = f"'{clean_query}' araması"

        # 2. İsimle bulunamadıysa Kategori Arama
        if not products_list and not found_title:
            target_cat = next((cat for cat, words in kategoriler.items() for w in words if w in voice_query), None)
            if target_cat:
                found_title = target_cat
                cur.execute(base_sql + " WHERE v.category_name ILIKE %s" + group + order + limits, (f"%{target_cat}%",))
                rows = cur.fetchall()

        if rows:
            for row in rows:
                img = row[3] if row[3] else f"https://placehold.co/400?text={row[1]}"
                products_list.append({
                    'id': row[0], 'name': row[1], 'price': float(row[2]), 
                    'image': img, 'category': row[4], 
                    'rating': float(round(row[5], 1))
                })
            
            has_more = len(products_list) == 6
            msg = f"{found_title} bulundu."
            return jsonify({'status': 'success', 'products': products_list, 'message_text': msg})
        
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

# --- SESLİ KOMUT (DINLE) ---
@app.route('/dinle', methods=['POST'])
def dinle():
    global CURRENT_STATE, LAST_CATEGORY
    r = sr.Recognizer()
    command = ""
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            r.energy_threshold = 400; r.dynamic_energy_threshold = False; r.pause_threshold = 0.8
            print("🎤 Dinliyorum..."); audio = r.listen(source, timeout=5, phrase_time_limit=8)
            command = r.recognize_google(audio, language='tr-tr').lower()
            
            response = {'status': 'success', 'command': command, 'message': f"Algılanan: {command}", 'state': CURRENT_STATE}
            
            # GENEL KOMUTLAR
            if "çıkış" in command or "oturumu kapat" in command:
                response.update({"action": "redirect", "redirect_url": "/logout", "message": "Çıkış yapılıyor."})
                return jsonify(response)

            if CURRENT_STATE == "MAIN_MENU":
                if "sepet" in command: response.update({"state": "OPEN_CART", "action": "redirect", "redirect_url": "/cart"})
                elif "hesabım" in command: response.update({"state": "ACCOUNT", "action": "redirect", "redirect_url": "/account"})
                elif "market" in command: response.update({"state": "MARKET", "action": "redirect", "redirect_url": "/market"})
                elif "ürün" in command or "al" in command:
                    CURRENT_STATE = "SEARCH"; response.update({"state": "SEARCH", "message": "Ne almak istersiniz?"})
            
            elif CURRENT_STATE == "SEARCH":
                cat = next((c for c, w in kategoriler.items() for k in w if k in command), None)
                if cat:
                    LAST_CATEGORY = cat; CURRENT_STATE = "CATEGORY_CONFIRM"
                    response.update({"state": "CATEGORY_CONFIRM", "category": cat, "message": f"{cat} bulundu, listeliyim mi?"})
                else:
                    response.update({"state": "SEARCH", "message": "Kategori anlaşılamadı, ürün aranıyor..."})
            
            elif CURRENT_STATE == "CATEGORY_CONFIRM":
                if "evet" in command or "listele" in command:
                    CURRENT_STATE = "LIST_PRODUCTS"; response.update({"state": "LIST_PRODUCTS", "query": LAST_CATEGORY})
                else:
                    CURRENT_STATE = "MAIN_MENU"; response.update({"state": "MAIN_MENU", "message": "İptal edildi."})

            return jsonify(response)
    except: return jsonify({'status': 'error', 'message': "Anlaşılamadı."})

if __name__ == '__main__':
    app.run(debug=True)