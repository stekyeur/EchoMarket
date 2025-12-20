from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import speech_recognition as sr
import psycopg2
import bcrypt
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = 'cok_gizli_anahtar'

def get_db_connection():
    # SSL gerekirse sslmode='require' ekle
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# --- GELİŞMİŞ SES TANIMA ---
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            # 1. Ortam gürültüsünü dinleyip kalibre et (1 saniye bekle)
            print("Gürültü kalibrasyonu yapılıyor...")
            r.adjust_for_ambient_noise(source, duration=1)
            
            # 2. Enerji eşiğini artır (Daha kararlı dinleme için)
            r.energy_threshold = 400 
            r.dynamic_energy_threshold = True
            
            print("Dinliyorum...")
            # timeout: Ses gelmeye başlamazsa kaç saniye beklesin (5 sn yaptık)
            # phrase_time_limit: Konuşma ne kadar sürebilir (10 sn yaptık - uzun cümleler için)
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            
            text = r.recognize_google(audio, language='tr-tr').lower()
            print(f"Algılanan: {text}")
            return text

        except sr.WaitTimeoutError:
            print("Süre doldu, ses algılanmadı.")
            return None
        except sr.UnknownValueError:
            print("Ses anlaşılamadı.")
            return None
        except Exception as e:
            print(f"Mikrofon Hatası: {e}")
            return None

# --- ROTALAR ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dinle', methods=['POST'])
def dinle():
    command = recognize_speech()
    action = "none"
    redirect_url = ""
    message = "Ses algılanamadı veya anlaşılamadı."
    status = "error"

    if command:
        status = "success"
        message = f"Algılanan: {command}"
        
        # Yönlendirme Komutları
        if 'giriş' in command:
            action = "redirect"
            redirect_url = "/login"
        elif 'kayıt' in command:
            action = "redirect"
            redirect_url = "/register"
        elif 'market' in command or 'alışveriş' in command:
            action = "redirect"
            redirect_url = "/market"
        elif 'sepet' in command:
            action = "redirect"
            redirect_url = "/cart"
        elif 'hesabım' in command or 'profil' in command:
            action = "redirect"
            redirect_url = "/account"
        
        # Arama Komutları
        elif 'ara' in command or 'bul' in command:
            term = command.replace('ara', '').replace('bul', '').replace('getir', '').strip()
            action = "redirect"
            redirect_url = f"/market?q={term}"

    return jsonify({'status': status, 'command': command, 'action': action, 'redirect_url': redirect_url, 'message': message})

# GİRİŞ YAP
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, password FROM "user" WHERE email = %s', (email,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['user_id'] = user[0]
            session['name'] = user[1]
            return jsonify({'status': 'success', 'redirect': '/market'})
        
        return jsonify({'status': 'error', 'message': 'Hatalı bilgi.'})

    return render_template('login.html')

# KAYIT OL
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Kullanıcı Ekle
            cur.execute(
                'INSERT INTO "user" (name, email, password, phone) VALUES (%s, %s, %s, %s) RETURNING id',
                (data.get('full_name'), data.get('email'), data.get('password'), data.get('phone'))
            )
            new_user_id = cur.fetchone()[0]
            
            # Adres Ekle
            if data.get('street') or data.get('city'):
                cur.execute(
                    'INSERT INTO address (userid, street, city, zipcode) VALUES (%s, %s, %s, %s)',
                    (new_user_id, data.get('street'), data.get('city'), data.get('zipcode'))
                )
            
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Kayıt başarılı!'})
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)})
        finally:
            conn.close()

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
    conn.close()
    
    # HTML'e GEREKLİ TÜM DEĞİŞKENLERİ GÖNDERİYORUZ
    return render_template('market.html', products=products, current_page=page, search_query=search_query)

# SEPETİM
# --- MEVCUT 'cart' ROTASINI BUNUNLA DEĞİŞTİR ---
# (Değişiklik sebebi: SQL sorgusuna 'p.id' eklendi, böylece butonlar hangi ürünü güncelleyeceğini bilir)
@app.route('/cart')
def cart():
    if 'user_id' not in session: return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Sepeti Bul
    cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
    session_row = cur.fetchone()
    
    cart_items = []
    total_amount = 0
    
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
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)

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
            return jsonify({'status': 'success'})
        
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
    if 'user_id' not in session: return redirect('/login')
    
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
# 1. AJAX Ürün Arama (Sayfa yenilenmeden arama yapar)
@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    query = data.get('query', '')
    offset = data.get('offset', 0)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Arama terimini hazırla
        search_term = f"%{query}%"
        
        # Hem isimde hem kategoride ara
        sql = """
            SELECT id, name, price, image_url 
            FROM view_product_summary 
            WHERE name ILIKE %s OR category_name ILIKE %s
            ORDER BY id 
            LIMIT 4 OFFSET %s
        """
        cur.execute(sql, (search_term, search_term, offset))
        rows = cur.fetchall()
        
        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'image': row[3]
            })
            
        if products:
            return jsonify({'status': 'success', 'products': products})
        else:
            return jsonify({'status': 'empty'})
            
    except Exception as e:
        print(f"Arama Hatası: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

# 2. AJAX Sepete Ekleme (Sayfa yenilenmeden ekler)
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart_ajax():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapmalısınız'})

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
        return jsonify({'status': 'success'})
        
    except Exception as e:
        conn.rollback()
        print(f"Sepet Hatası: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()
if __name__ == '__main__':
    app.run(debug=True)