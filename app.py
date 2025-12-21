from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import speech_recognition as sr
import psycopg2
import bcrypt
from datetime import datetime
from config import DB_CONFIG

CURRENT_STATE = "MAIN_MENU"
LAST_CATEGORY = None
app = Flask(__name__)
# Bu anahtarın sabit olması, sunucu yeniden başladığında oturumun düşmemesi için önemlidir.
app.secret_key = "cok_gizli_anahtar_sabit_kalsin"

# --- VERİTABANI BAĞLANTISI ---
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, sslmode='require')
    return conn

# --- YARDIMCI: Sepet Sayısını Getir ---
def get_cart_count(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (user_id,))
        session_row = cur.fetchone()

        if session_row:
            session_id = session_row[0]
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

@app.route('/market')
def market():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')

    conn = get_db_connection()
    cur = conn.cursor()
    offset = (page - 1) * 6

    if search_query:
        cur.execute("SELECT * FROM view_product_summary WHERE name ILIKE %s LIMIT 6 OFFSET %s", (f"%{search_query}%", offset))
    else:
        cur.execute("SELECT * FROM view_product_summary ORDER BY id LIMIT 6 OFFSET %s", (offset,))

    products = cur.fetchall()

    cart_count = 0
    if 'user_id' in session:
        cart_count = get_cart_count(session['user_id'])

    conn.close()
    return render_template('market.html', products=products, current_page=page, search_query=search_query, cart_count=cart_count)

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
    session_row = cur.fetchone()

    cart_items = []
    total_amount = 0
    cart_count = get_cart_count(session['user_id'])

    if session_row:
        session_id = session_row[0]
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

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart_ajax():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
        res = cur.fetchone()

        if res:
            session_id = res[0]
        else:
            cur.execute('INSERT INTO shoppingsession (userid) VALUES (%s) RETURNING id', (session['user_id'],))
            session_id = cur.fetchone()[0]

        cur.execute('SELECT id, quantity FROM cartitem WHERE sessionid=%s AND productid=%s', (session_id, product_id))
        existing = cur.fetchone()

        if existing:
            new_qty = existing[1] + quantity
            cur.execute('UPDATE cartitem SET quantity=%s WHERE id=%s', (new_qty, existing[0]))
        else:
            cur.execute('INSERT INTO cartitem (sessionid, productid, quantity) VALUES (%s, %s, %s)', (session_id, product_id, quantity))

        conn.commit()
        new_cart_count = get_cart_count(session['user_id'])
        return jsonify({'status': 'success', 'cart_count': new_cart_count})

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapın'})

    data = request.get_json()
    product_id = data.get('product_id')
    action = data.get('action')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
        res = cur.fetchone()
        if not res: return jsonify({'status': 'error'})
        session_id = res[0]

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
                cur.execute('DELETE FROM cartitem WHERE sessionid=%s AND productid=%s', (session_id, product_id))

            conn.commit()
            new_cart_count = get_cart_count(session['user_id'])
            return jsonify({'status': 'success', 'cart_count': new_cart_count})

        return jsonify({'status': 'error', 'message': 'Ürün bulunamadı'})

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

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
            return jsonify({"status": "success", "cart_count": 0})
    except:
        return jsonify({"status": "error"})
    finally:
        conn.close()

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    message = None
    message_type = "success"

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        new_password = request.form.get('new_password')
        street = request.form.get('street')
        city = request.form.get('city')
        zipcode = request.form.get('zipcode')

        try:
            cur.execute('UPDATE "user" SET name=%s, phone=%s, email=%s WHERE id=%s',
                        (name, phone, email, session['user_id']))

            if new_password and new_password.strip():
                hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute('UPDATE "user" SET password=%s WHERE id=%s', (hashed_pw, session['user_id']))

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

    cur.execute('SELECT name, email, phone FROM "user" WHERE id = %s', (session['user_id'],))
    user_info = cur.fetchone()

    cur.execute('SELECT street, city, zipcode FROM address WHERE userid = %s', (session['user_id'],))
    address_info = cur.fetchone()

    cur.execute('SELECT id, totalamount, orderdate, status FROM "Order" WHERE userid = %s ORDER BY orderdate DESC', (session['user_id'],))
    orders = cur.fetchall()

    # --- YENİ EKLENEN KISIM: Sepet Sayısı ---
    cart_count = get_cart_count(session['user_id'])

    conn.close()

    addr_data = address_info if address_info else ("", "", "")

    return render_template('account.html', user=user_info, address=addr_data, orders=orders, msg=message, msg_type=message_type, cart_count=cart_count)

@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    voice_query = data.get('query', '').lower()
    offset = data.get('offset', 0)
    is_cheapest = "en ucuz" in voice_query or "uygun" in voice_query
    clean_query = voice_query.replace("en ucuz", "").replace("uygun", "").strip()

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        products_list = []
        found_title = None

        limit_clause = f" LIMIT 6 OFFSET {offset}"
        order_clause = " ORDER BY price ASC" if is_cheapest else " ORDER BY id"

        # Strateji 1: İsim Arama
        sql_product = f"SELECT id, name, price FROM product WHERE name ILIKE %s {order_clause} {limit_clause}"
        cur.execute(sql_product, (f"%{clean_query}%",))
        rows = cur.fetchall()

        if rows:
            found_title = f"'{clean_query}' araması"
            for row in rows:
                products_list.append({'id': row[0], 'name': row[1], 'price': float(row[2])})

        # Strateji 2: Kategori Arama
        else:
            target_category = None
            for kategori_adi, anahtar_kelimeler in kategoriler.items():
                for kelime in anahtar_kelimeler:
                    if kelime in voice_query:
                        target_category = kategori_adi
                        break
                if target_category: break

            if target_category:
                cur.execute("SELECT id, name FROM category WHERE name ILIKE %s", (f"%{target_category}%",))
                cat_row = cur.fetchone()

                if cat_row:
                    cat_id = cat_row[0]
                    found_title = cat_row[1]
                    sql_cat = f"SELECT id, name, price FROM product WHERE categoryid = %s {order_clause} {limit_clause}"
                    cur.execute(sql_cat, (cat_id,))
                    rows = cur.fetchall()
                    for row in rows:
                        products_list.append({'id': row[0], 'name': row[1], 'price': float(row[2])})

        if products_list:
            final_products = []
            for p in products_list:
                fake_image_url = f"https://placehold.co/400x300/e6e6e6/000000?text={p['name'].replace(' ', '+')}"
                final_products.append({
                    'id': p['id'],
                    'name': p['name'],
                    'price': p['price'],
                    'image': fake_image_url
                })
            has_more = len(final_products) == 6
            msg = f"{found_title} bulundu."
            return jsonify({'status': 'success', 'products': final_products, 'category_name': found_title, 'has_more': has_more, 'message_text': msg})
        else:
            return jsonify({'status': 'empty', 'message': 'Ürün bulunamadı.'})

    except Exception as e:
        print(f"Arama Hatası: {e}")
        return jsonify({'status': 'error', 'message': 'Veritabanı hatası.'})
    finally:
        if conn: conn.close()

# --- DÜZELTİLMİŞ /dinle FONKSİYONU ---
@app.route('/dinle', methods=['POST'])
def dinle():
    global CURRENT_STATE, LAST_CATEGORY
    r = sr.Recognizer()
    command = ""
    status = "error"
    message = "Ses algılanamadı."

    try:
        with sr.Microphone() as source:
            r.energy_threshold = 400
            r.dynamic_energy_threshold = False
            r.pause_threshold = 0.8
            print("🎤 Python: Dinliyorum (Gecikmesiz)...")

            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            command = r.recognize_google(audio, language='tr-tr').lower()
            print(f"🗣 Algılanan: {command}")
            status = "success"
            message = f"Algılanan: {command}"

            # --- DÜZELTME: Cevap Objesi ---
            # 'command' verisini HER ZAMAN gönderiyoruz.
            response_data = {
                'status': 'success',
                'command': command,
                'message': message,
                'state': CURRENT_STATE
            }

            # --- KOMUT İŞLEME ---
            if CURRENT_STATE == "MAIN_MENU":
                if "sepet" in command:
                    response_data.update({"state": "OPEN_CART", "message": "Sepetinizi açıyorum."})
                    return jsonify(response_data)

                if "hesabım" in command:
                    response_data.update({"state": "ACCOUNT", "message": "Hesabınıza bakılıyor."})
                    return jsonify(response_data)

                if "ürün" in command or "al" in command:
                    CURRENT_STATE = "SEARCH"
                    response_data.update({"state": "SEARCH", "message": "Ne almak istiyorsunuz?"})
                    return jsonify(response_data)

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
                    response_data.update({"state": "CATEGORY_CONFIRM", "category": found_category, "message": f"{found_category} kategorisi bulundu. Listeleyeyim mi?"})
                    return jsonify(response_data)

                response_data.update({"state": "SEARCH", "message": "Uygun kategori bulamadım."})
                return jsonify(response_data)

            if CURRENT_STATE == "CATEGORY_CONFIRM":
                if "hayır" in command:
                    CURRENT_STATE = "MAIN_MENU"
                    response_data.update({"state": "MAIN_MENU", "message": "İptal edildi."})
                    return jsonify(response_data)
                if "evet" in command or "listele" in command:
                    CURRENT_STATE = "LIST_PRODUCTS"
                    response_data.update({"state": "LIST_PRODUCTS", "query": LAST_CATEGORY})
                    return jsonify(response_data)

            return jsonify(response_data)

    except sr.WaitTimeoutError:
        return jsonify({'status': 'error', 'message': "Süre doldu."})
    except sr.UnknownValueError:
        return jsonify({'status': 'error', 'message': "Anlayamadım."})
    except Exception as e:
        print(f"KRİTİK HATA: {e}")
        return jsonify({'status': 'error', 'message': "Sistem hatası."})

# --- CHECKOUT ve SUCCESS ROTALARI ---

@app.route('/checkout', methods=['POST'])
def checkout_action():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapmalısınız'})

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT id FROM shoppingsession WHERE userid = %s', (session['user_id'],))
        sid_row = cur.fetchone()

        if not sid_row:
            return jsonify({'status': 'error', 'message': 'Sepet oturumu bulunamadı'})

        session_id = sid_row[0]

        cur.execute("""
                    SELECT ci.productid, ci.quantity, p.price
                    FROM cartitem ci
                             JOIN product p ON ci.productid = p.id
                    WHERE ci.sessionid = %s
                    """, (session_id,))

        items = cur.fetchall()

        if not items:
            return jsonify({'status': 'error', 'message': 'Sepetiniz boş'})

        total_amount = sum(item[1] * item[2] for item in items)

        cur.execute("""
                    INSERT INTO "Order" (userid, orderdate, totalamount, status)
                    VALUES (%s, %s, %s, 'Hazırlanıyor')
                        RETURNING id
                    """, (session['user_id'], datetime.now().date(), total_amount))

        new_order_id = cur.fetchone()[0]

        for item in items:
            p_id = item[0]
            qty = item[1]
            price = item[2]

            cur.execute("""
                        INSERT INTO orderitem (orderid, productid, quantity, price)
                        VALUES (%s, %s, %s, %s)
                        """, (new_order_id, p_id, qty, price))

        cur.execute("DELETE FROM cartitem WHERE sessionid = %s", (session_id,))

        conn.commit()
        return jsonify({'status': 'success', 'order_id': new_order_id})

    except Exception as e:
        conn.rollback()
        print(f"Sipariş Hatası: {e}")
        return jsonify({'status': 'error', 'message': f'Sipariş oluşturulamadı: {str(e)}'})
    finally:
        conn.close()

@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
                SELECT id, totalamount, orderdate, status
                FROM "Order"
                WHERE id = %s AND userid = %s
                """, (order_id, session['user_id']))
    order = cur.fetchone()

    if not order:
        return "Sipariş bulunamadı", 404

    cur.execute("""
                SELECT p.name, oi.quantity, oi.price, p.image_url
                FROM orderitem oi
                         JOIN product p ON oi.productid = p.id
                WHERE oi.orderid = %s
                """, (order_id,))
    order_items = cur.fetchall()
    cart_count = get_cart_count(session['user_id'])
    conn.close()
    return render_template('order_success.html', order=order, items=order_items, cart_count=cart_count)

if __name__ == '__main__':
    app.run(debug=True)