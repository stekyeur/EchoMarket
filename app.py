from flask import Flask, render_template, jsonify, request
import speech_recognition as sr
import psycopg2
import bcrypt
from config import DB_CONFIG

app = Flask(__name__)

# --- VERİTABANI BAĞLANTISI ---
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, sslmode='require')
    return conn

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
    return render_template('market.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_name = data.get('name')
    price = data.get('price')
    print(f"🛒 SEPETE EKLENDİ (SİMÜLASYON): {product_name} - {price} TL")
    return jsonify({'status': 'success', 'message': f'{product_name} sepete eklendi.'})

@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    voice_query = data.get('query', '').lower()
    offset = data.get('offset', 0)

    target_category = None
    for kategori_adi, anahtar_kelimeler in kategoriler.items():
        for kelime in anahtar_kelimeler:
            if kelime in voice_query:
                target_category = kategori_adi
                break
        if target_category: break

    is_cheapest = "en ucuz" in voice_query or "uygun" in voice_query

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        products_list = []
        found_category_name = None

        limit_clause = f" LIMIT 4 OFFSET {offset}"
        order_clause = " ORDER BY price ASC" if is_cheapest else ""

        if target_category:
            cur.execute("SELECT id, name FROM category WHERE name ILIKE %s", (f"%{target_category}%",))
            cat_row = cur.fetchone()
            if cat_row:
                cat_id = cat_row[0]
                found_category_name = cat_row[1]
                sql = f"SELECT name, price FROM product WHERE categoryid = %s {order_clause} {limit_clause}"
                cur.execute(sql, (cat_id,))
                rows = cur.fetchall()
                for row in rows:
                    products_list.append({'name': row[0], 'price': float(row[1])})

        if not products_list:
            clean_query = voice_query.replace("en ucuz", "").replace("ürünleri", "").strip()
            sql = f"SELECT name, price FROM product WHERE name ILIKE %s {order_clause} {limit_clause}"
            cur.execute(sql, (f"%{clean_query}%",))
            rows = cur.fetchall()
            for row in rows:
                products_list.append({'name': row[0], 'price': float(row[1])})
            if products_list:
                found_category_name = f"'{clean_query}' araması"

        if products_list:
            final_products = []
            for p in products_list:
                p_name = p['name']
                p_price = p['price']
                fake_image_url = f"https://placehold.co/400x300/e6e6e6/000000?text={p_name.replace(' ', '+')}"
                final_products.append({'name': p_name, 'price': p_price, 'image': fake_image_url})

            has_more = len(final_products) == 4

            msg = f"{found_category_name} bulundu."
            return jsonify({
                'status': 'success',
                'products': final_products,
                'category_name': found_category_name,
                'has_more': has_more,
                'message_text': msg
            })
        else:
            msg = "Başka ürün bulunamadı." if offset > 0 else "Ürün bulunamadı."
            return jsonify({'status': 'empty', 'message': msg})

    except Exception as e:
        print(f"Arama Hatası: {e}")
        return jsonify({'status': 'error', 'message': 'Veritabanı hatası.'})
    finally:
        if conn: conn.close()

# --- SES TANIMA (HIZLI & GECİKMESİZ) ---
@app.route('/dinle', methods=['POST'])
def dinle():
    r = sr.Recognizer()
    command = ""
    status = "error"
    message = "Ses algılanamadı."
    try:
        with sr.Microphone() as source:
            # 🚀 HIZLANDIRMA: Gürültü ayarını kapattık. Direkt dinleyecek.
            # adjust_for_ambient_noise fonksiyonu 0.5-1 sn bekletiyordu, kaldırdık.

            # Hassasiyet ayarları (Manuel)
            r.energy_threshold = 400  # Ses eşiği
            r.dynamic_energy_threshold = False # Otomatik ayarı kapat
            r.pause_threshold = 0.8   # Susma süresi (daha kısa tutarak hızlı cevap verir)

            print("🎤 Python: Dinliyorum (Gecikmesiz)...")

            # Timeout: Ses gelmesini bekleme süresi (10sn yaptık)
            # Phrase Limit: Konuşma süresi (10sn yaptık)
            audio = r.listen(source, timeout=10, phrase_time_limit=10)

            command = r.recognize_google(audio, language='tr-tr').lower()
            print(f"🗣 Algılanan: {command}")
            status = "success"
            message = f"Algılanan: {command}"
    except sr.WaitTimeoutError:
        message = "Süre doldu, ses gelmedi."
    except sr.UnknownValueError:
        message = "Ne dediğinizi anlayamadım."
    except Exception as e:
        message = f"Hata: {str(e)}"

    return jsonify({'status': status, 'command': command, 'message': message})


if __name__ == '__main__':
    app.run(debug=True)