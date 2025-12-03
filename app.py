from flask import Flask, render_template, jsonify, request
import speech_recognition as sr
import psycopg2
import bcrypt  # GÜVENLİK İÇİN EKLENDİ
from config import DB_CONFIG

app = Flask(__name__)

# --- VERİTABANI BAĞLANTISI ---
def get_db_connection():
    # Supabase (Bulut) bağlantısı
    conn = psycopg2.connect(**DB_CONFIG, sslmode='require')
    return conn

# --- ROTALAR ---

# 1. KARŞILAMA EKRANI
@app.route('/')
def index():
    return render_template('index.html')

# 2. GİRİŞ İŞLEMLERİ (GÜVENLİ)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password') # Kullanıcının girdiği düz şifre (örn: anam1205)

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Sadece E-postaya göre kullanıcıyı buluyoruz
            cur.execute('SELECT id, password, name FROM "user" WHERE email = %s', (email,))
            user = cur.fetchone() # (id, hashed_password, name) döner

            cur.close()
            conn.close()

            if user:
                # Veritabanındaki hashli şifre (örn: $2a$06$...)
                stored_password_hash = user[1]

                # Bcrypt ile kontrol et: Girilen şifre == Hashlenmiş şifre mi?
                # encode('utf-8') ile byte formatına çeviriyoruz çünkü bcrypt böyle çalışır
                if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                    print(f">>> BAŞARILI: Hoş geldin {user[2]}")
                    return jsonify({'status': 'success', 'message': 'Giriş başarılı!'})
                else:
                    print(">>> BAŞARISIZ: Şifre yanlış.")
                    return jsonify({'status': 'error', 'message': 'E-posta veya şifre hatalı.'})
            else:
                print(">>> BAŞARISIZ: Kullanıcı bulunamadı.")
                return jsonify({'status': 'error', 'message': 'E-posta veya şifre hatalı.'})

        except Exception as e:
            print(f"!!! LOGIN HATASI: {e}")
            return jsonify({'status': 'error', 'message': 'Sunucu hatası.'})

    return render_template('login.html')

# 3. KAYIT İŞLEMLERİ (GÜVENLİ - HASHLEME EKLENDİ)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()

        name = data.get('full_name')
        email = data.get('email')
        plain_password = data.get('password') # Düz şifre
        phone = data.get('phone')

        street = data.get('street')
        city = data.get('city')
        zipcode = data.get('zipcode')

        # ŞİFREYİ HASHLEME (KARIŞTIRMA)
        # Veritabanına asla düz şifre kaydetmeyiz!
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Kullanıcı Kaydı (Hashlenmiş şifreyi gönderiyoruz)
            cur.execute(
                'INSERT INTO "user" (name, email, password, phone) VALUES (%s, %s, %s, %s) RETURNING id',
                (name, email, hashed_password, phone)
            )
            new_user_id = cur.fetchone()[0]
            print(f"Kullanıcı ID oluşturuldu: {new_user_id}")

            # Adres Kaydı
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
            print(">>> HATA: Bu e-posta zaten kayıtlı.")
            return jsonify({'status': 'error', 'message': 'Bu e-posta kayıtlı.'})
        except Exception as e:
            if conn: conn.rollback()
            print(f"!!! KAYIT HATASI: {e}")
            return jsonify({'status': 'error', 'message': f'Hata: {str(e)}'})
        finally:
            if conn: conn.close()

    return render_template('register.html')

# 4. MARKET EKRANI
@app.route('/market')
def market():
    return render_template('market.html')

# 5. ÜRÜN ARAMA
@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    voice_query = data.get('query', '').lower()

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM category WHERE name ILIKE %s", (f"%{voice_query}%",))
        category = cur.fetchone()

        products_list = []

        if category:
            cat_id = category[0]
            cur.execute("SELECT name, price FROM products WHERE categoryid = %s LIMIT 4", (cat_id,))
            rows = cur.fetchall()

            for row in rows:
                p_name = row[0]
                p_price = float(row[1])
                fake_image_url = f"https://placehold.co/400x300/e6e6e6/000000?text={p_name.replace(' ', '+')}"

                products_list.append({
                    'name': p_name,
                    'price': p_price,
                    'image': fake_image_url
                })

            return jsonify({'status': 'success', 'products': products_list})
        else:
            return jsonify({'status': 'error', 'message': 'Kategori bulunamadı.'})

    except Exception as e:
        print(f"Arama Hatası: {e}")
        return jsonify({'status': 'error', 'message': 'Veritabanı hatası.'})
    finally:
        if conn: conn.close()

# --- SES TANIMA API ---
r = sr.Recognizer()

@app.route('/dinle', methods=['POST'])
def dinle():
    command = ""
    status = "error"
    message = "Ses algılanamadı."

    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Python: Dinliyorum...")
            audio = r.listen(source, timeout=4, phrase_time_limit=5)
            command = r.recognize_google(audio, language='tr-tr').lower()
            print(f"🗣 Algılanan: {command}")
            status = "success"
            message = f"Algılanan: {command}"
    except Exception as e:
        message = f"Hata: {str(e)}"

    return jsonify({'status': status, 'command': command, 'message': message})

if __name__ == '__main__':
    app.run(debug=True)