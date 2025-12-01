from flask import Flask, render_template, jsonify, request
import speech_recognition as sr
import psycopg2
from config import DB_CONFIG

app = Flask(__name__)

# --- VERİTABANI BAĞLANTISI ---
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, sslmode='require')
    return conn

# --- ROTALAR (GÜNCELLENDİ) ---

# 1. KARŞILAMA EKRANI (Açılış Sayfası)
@app.route('/')
def index():
    return render_template('index.html')

# 2. GİRİŞ YAP EKRANI
@app.route('/login')
def login():
    return render_template('login.html')

# 3. KAYIT OL EKRANI
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()

        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO users (full_name, email, password, phone) VALUES (%s, %s, %s, %s)',
                        (full_name, email, password, phone))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Kayıt başarılı!'})
        except psycopg2.IntegrityError:
            return jsonify({'status': 'error', 'message': 'Bu e-posta zaten kayıtlı.'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Sunucu hatası.'})

    return render_template('register.html')

# --- SES TANIMA API (Standart) ---
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