import os
import pandas as pd
import psycopg2
from psycopg2 import extras
import random
from config import DB_CONFIG

# --- DİNAMİK KLASÖR AYARLARI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URUN_KLASORU = os.path.join(BASE_DIR, "txtler")
USER_KLASORU = os.path.join(BASE_DIR, "txt_2")

KULLANICI_DOSYASI = "kullanici_verileri.txt"
ADRES_DOSYASI = "address_data.txt"

# --- YARDIMCI FONKSİYONLAR ---
def clean_price(price):
    try: return float(str(price).replace('TL', '').replace('"', '').replace('.', '').replace(',', '.').strip())
    except: return 0.0

def clean_rating(rating):
    try: return float(str(rating).replace(',', '.'))
    except: return None

def clean_reviews(reviews):
    try: return int(str(reviews).replace('(', '').replace(')', '').replace('.', ''))
    except: return 0

# --- 1. TABLOLARI OLUŞTURMA ---
def create_tables(cursor):
    print("🔨 Tablolar sıfırlanıyor...")
    
    # pgcrypto eklentisini Python'dan da garantiye alalım
    cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;") 

    tables = ["productrating", "orderitem", "\"order\"", "product", "address", "\"user\"", "category"]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    
    # TRIGGER FONKSİYONUNU OLUŞTUR (SQL'deki işi burada yapıyoruz)
    cursor.execute("""
        CREATE OR REPLACE FUNCTION hash_password() RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.password NOT LIKE '$2a$%' AND NEW.password NOT LIKE '$2b$%' THEN
                NEW.password := crypt(NEW.password, gen_salt('bf'));
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    sqls = [
        """CREATE TABLE category (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL);""",
        """CREATE TABLE "user" (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, email VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, phone VARCHAR(50));""",
        """CREATE TABLE address (id SERIAL PRIMARY KEY, userid INT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE, street VARCHAR(255), city VARCHAR(100), zipcode VARCHAR(20));""",
        """CREATE TABLE product (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, description TEXT, price FLOAT NOT NULL, stock INT NOT NULL DEFAULT 0, categoryid INT NOT NULL REFERENCES category(id), unitofmeasure VARCHAR(50));""",
        """CREATE TABLE "order" (id SERIAL PRIMARY KEY, userid INT NOT NULL REFERENCES "user"(id), orderdate DATE NOT NULL, totalamount FLOAT, status VARCHAR(50));""",
        """CREATE TABLE orderitem (orderid INT NOT NULL REFERENCES "order"(id), productid INT NOT NULL REFERENCES product(id), quantity INT NOT NULL, price FLOAT NOT NULL, PRIMARY KEY (orderid, productid));""",
        """CREATE TABLE productrating (userid INT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE, productid INT NOT NULL REFERENCES product(id) ON DELETE CASCADE, rating INT CHECK (rating >= 1 AND rating <= 5), ratedate TIMESTAMP DEFAULT NOW(), PRIMARY KEY (userid, productid));"""
    ]
    
    for sql in sqls:
        cursor.execute(sql)
        
    # TRIGGER'I TABLOYA BAĞLA
    cursor.execute("""
        CREATE TRIGGER trigger_hash_password
        BEFORE INSERT OR UPDATE ON "user"
        FOR EACH ROW EXECUTE FUNCTION hash_password();
    """)
    
    print("✅ Tablolar ve Trigger hazır.")

# --- 2. KULLANICI VE ADRES YÜKLEME ---
def import_users_and_addresses(cursor):
    print("\n👤 Kullanıcılar (Şifresiz gönderiliyor -> Trigger şifreleyecek)...")
    
    u_path = os.path.join(USER_KLASORU, KULLANICI_DOSYASI)
    if os.path.exists(u_path):
        df = pd.read_csv(u_path)
        has_phone = 'Phone' in df.columns
        users_data = []
        
        for _, row in df.iterrows():
            phone = str(row['Phone']) if has_phone and pd.notna(row['Phone']) else None
            # DİKKAT: Şifreyi (row['Password']) olduğu gibi, DÜZ HALİYLE gönderiyoruz.
            users_data.append((row['id'], row['Name'], row['Email'], row['Password'], phone))
            
        extras.execute_values(cursor, 
            """INSERT INTO "user" (id, name, email, password, phone) VALUES %s ON CONFLICT DO NOTHING""",
            users_data)
        
        cursor.execute("SELECT setval(pg_get_serial_sequence('\"user\"', 'id'), (SELECT MAX(id) FROM \"user\") + 1)")
        print(f"   -> {len(users_data)} kullanıcı eklendi.")

    a_path = os.path.join(USER_KLASORU, ADRES_DOSYASI)
    if os.path.exists(a_path):
        df = pd.read_csv(a_path)
        addr_data = []
        for _, row in df.iterrows():
            addr_data.append((row['UserID'], row['Street'], row['City'], row['ZipCode']))
            
        extras.execute_values(cursor,
            """INSERT INTO address (userid, street, city, zipcode) VALUES %s""",
            addr_data)
        print(f"   -> {len(addr_data)} adres eklendi.")

# --- 3. KATEGORİ VE ÜRÜN ---
def import_products(cursor):
    print("\n📦 Ürünler yükleniyor...")
    if not os.path.exists(URUN_KLASORU): return
    
    total_products = 0
    for filename in os.listdir(URUN_KLASORU):
        if filename.endswith(".txt"):
            cat_name = filename.replace(".txt", "")
            cursor.execute("INSERT INTO category (name) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id", (cat_name,))
            res = cursor.fetchone()
            cat_id = res[0] if res else cursor.execute("SELECT id FROM category WHERE name = %s", (cat_name,)) or cursor.fetchone()[0]
            
            df = pd.read_csv(os.path.join(URUN_KLASORU, filename), on_bad_lines='skip')
            prod_data = []
            for _, row in df.iterrows():
                name = str(row['Name'])
                if pd.isna(name): continue
                price = clean_price(row.get('Price'))
                stock = random.randint(0, 50)
                prod_data.append((name, name, price, stock, cat_id, 'Adet'))
            
            if prod_data:
                extras.execute_values(cursor, """INSERT INTO product (name, description, price, stock, categoryid, unitofmeasure) VALUES %s ON CONFLICT DO NOTHING""", prod_data)
                total_products += len(prod_data)
    print(f"✅ {total_products} ürün yüklendi.")

# --- 4. RATING ---
def generate_ratings(cursor):
    print("\n⭐ Oylar dağıtılıyor...")
    cursor.execute('SELECT id FROM "user"')
    user_ids = [r[0] for r in cursor.fetchall()]
    cursor.execute('SELECT name, id FROM product')
    prod_map = {r[0]: r[1] for r in cursor.fetchall()}
    
    ratings_batch = []
    for filename in os.listdir(URUN_KLASORU):
        if filename.endswith(".txt"):
            df = pd.read_csv(os.path.join(URUN_KLASORU, filename), on_bad_lines='skip')
            for _, row in df.iterrows():
                p_name = str(row['Name'])
                if p_name not in prod_map: continue
                target = clean_rating(row.get('Rating'))
                count = clean_reviews(row.get('Reviews'))
                if not target or count == 0: continue
                
                limit = min(count, len(user_ids))
                chosen_users = random.sample(user_ids, limit)
                pid = prod_map[p_name]
                base_rating = int(target)
                prob = target - base_rating
                
                for uid in chosen_users:
                    score = base_rating + 1 if random.random() < prob else base_rating
                    ratings_batch.append((uid, pid, score))
    
    if ratings_batch:
        extras.execute_values(cursor, """INSERT INTO productrating (userid, productid, rating) VALUES %s ON CONFLICT DO NOTHING""", ratings_batch)
        print(f"✅ {len(ratings_batch)} oy işlendi.")

# --- MAIN ---
def main():
    conn = None
    try:
        params = DB_CONFIG.copy()
        if 'sslmode' not in params: params['sslmode'] = 'prefer'
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        print("🔌 Bağlandı.\n")
        
        create_tables(cursor) # Artık trigger'ı da bu fonksiyon kuruyor
        import_users_and_addresses(cursor)
        import_products(cursor)
        generate_ratings(cursor)
        
        conn.commit()
        print("\n🎉 KURULUM TAMAMLANDI! (Trigger sayesinde şifreler güvende) 🎉")
        
    except Exception as e:
        print("\n❌ HATA:", e)
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    main()