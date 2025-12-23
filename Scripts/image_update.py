import sys
import os
import psycopg2# --- 1. IMPORT HATASINI ÇÖZEN KISIM ---
# Bu kod, Python'a "Bir üst klasöre de bak, config.py orada" der.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Artık config dosyasını bulabilir
from config import DB_CONFIG
# --- 1. ERİŞİLEBİLİR GÖRSEL KÜTÜPHANESİ (YATAY & NET) ---
IMG_CIPS      = "https://i.nefisyemektarifleri.com/2023/09/28/hangi-cips-kac-kalori-1-adet-cips-kac-kalori.jpg"
IMG_DIS       = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSrQXIskY1DR2vtULTOJ6ctmow4a7dmnw4pgQ&s"
IMG_SABUN     = "https://cdn2.karaca.com/karaca-cms-uploads/evde_sabun7_b9f930c983.jpg"
IMG_BULASIK   = "https://www.bosch-yetkiliservisi.com/Statics/image/faydali-bilgiler/bulasik-makineleri/1.jpg"
IMG_DEODORANT = "https://cdn.cimri.io/image/1000x1000/rexona-shower-fresh-200-ml-kadin-sprey-deodorant-ve-men-xtra-cool-2x150-ml-erkek-sprey-deodorant_824283445.jpg"
IMG_ICECEK    = "https://kalecafe.com/wp-content/uploads/2019/06/kale-kafe-vitamin-bar.jpg"
IMG_CORBA     = "https://d17wu0fn6x6rgz.cloudfront.net/img/w/tarif/mgt/16_16_11zon-487.webp"
IMG_GEVREK    = "https://i.lezzet.com.tr/images-xxlarge-secondary/kahvaltilik-gevrekleri-kullanmanin-6-yaratici-yolu-a73f721f-b8e8-489c-9c04-80d7adcbe770.jpg"
IMG_KAHVALTI  = "https://blog.teknosa.com/wp-content/uploads/2023/11/turkish-breakfast-1.jpg"
IMG_KAHVE     = "https://i.nefisyemektarifleri.com/2023/08/31/kahve-cesitleri-nelerdir-turk-ve-dunya-kahveleri-resimli-listesi.jpg"
IMG_KAGIT     = "https://images.migrosone.com/tazedirekt/product/31021069/31021069_yan-ac49aa-680x454.jpg"
IMG_KEK       = "https://www.bizimmutfak.com.tr/wp-content/uploads/2023/09/mas-kek.jpg"
IMG_KONSERVE  = "https://revitanisantasi.com/wp-content/uploads/2021/04/konserve.jpg"
IMG_KURU_GIDA = "https://d17wu0fn6x6rgz.cloudfront.net/img/w/blok/d/kuru_bakliyatlar.webp"
IMG_CEREZ     = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQzMh0d1nAeB6V2ENw-e-juilhLLp6dQqhH3g&s"
IMG_MAKARNA   = "https://www.unileverfoodsolutions.com.tr/konsept-uygulamalarimiz/leziz-makarnalar/menulerin-vazgecilmezi-makarna-cesitleri/jcr:content/parsys/content/textimage_1588320095_716914658/image.img.png/1641325179321.png"
IMG_TEMIZLIK  = "https://www.unileverfoodsolutions.com.tr/konsept-uygulamalarimiz/leziz-makarnalar/menulerin-vazgecilmezi-makarna-cesitleri/jcr:content/parsys/content/textimage_1588320095_716914658/image.img.png/1641325179321.png"
IMG_BAR       = "https://www.macfit.com/wp-content/uploads/2022/08/protein-bar-tarifi-2.jpg"
IMG_SALCA     = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSxQZynXlgZi9Jw4SI53nrnkJyfyfYxSE8WjQ&s"
IMG_SAMPUAN   = "https://www.kocaelifikir.com/wp-content/uploads/2024/12/sampuan.webp"
IMG_SUT       = "https://www.alibabasut.com/wp-content/uploads/2021/12/gunluk_taze_inek_sutu.jpg"
IMG_YAG       = "https://www.kizilkaya.com.tr/media/7872/bitkisel-yag-tuketimi-saglikli-beslenme.jpeg"
IMG_SEKER     = "https://image.fanatik.com.tr/i/fanatik/75/0x410/62827e9d45d2a051587e4c0e.jpg"
IMG_TRAŞ      = "https://cdn.shopify.com/s/files/1/0215/6108/1928/files/geleneksel_tiras_large.png?v=1588681901"
IMG_UN        = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ433CxnpARKEyyReIlY7ZOamXOtsMsFTP64g&s"
IMG_CAMASIR   = "https://eniyimiz.tr/wp-content/uploads/2023/08/en-iyi-camasir-deterjani.jpeg"
IMG_CAY       = "https://static.daktilo.com/sites/1702/uploads/2025/12/15/kuru-cay-fiyatlari-yeniden-gundemde.jpg"
IMG_CIKOLATA  = "https://i.nefisyemektarifleri.com/2023/07/27/cikolata-yapimi-cesitleri-kalori-ve-besin-degerleri-faydalari-zararlari-1.jpg"
IMG_EKMEK     = "https://i.nefisyemektarifleri.com/2022/09/22/ekmek-cesitleri-turk-ve-dunya-mutfagindan-tarifler-1.jpg"
def fix_images_exact_categories():
    conn = None
    try:
        print("Veritabanına bağlanılıyor...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        category_map = {
            "Atıştırmalık": IMG_CIPS,
            "Cips": IMG_CIPS,
            "Kraker": IMG_CIPS,
            "Ağız Bakım": IMG_DIS,
            "Banyo Ürünleri": IMG_SABUN,
            "Bulaşık Makinesi Deterjanı": IMG_BULASIK,
            "Bulaşık Yıkama": IMG_BULASIK,
            "Deodorant": IMG_DEODORANT,
            "Gazsız İçecek": IMG_ICECEK,
            "Hazır Çorba": IMG_CORBA,
            "Kahvaltılık Gevrek": IMG_GEVREK,
            "Kahvaltılık": IMG_KAHVALTI,
            "Kahve": IMG_KAHVE,
            "Kağıt Havlu": IMG_KAGIT,
            "Tuvalet Kağıdı": IMG_KAGIT,
            "Kek": IMG_KEK,
            "Unlu Mamül": IMG_KEK,
            "Konserveler": IMG_KONSERVE,
            "Kuru Gıda": IMG_KURU_GIDA,
            "Kuruyemiş": IMG_CEREZ,
            "Makarna": IMG_MAKARNA,
            "Mutfak Banyo Temizlik": IMG_TEMIZLIK,
            "Protein Bar": IMG_BAR,
            "Salça": IMG_SALCA,
            "Saç Bakımı": IMG_SAMPUAN,
            "Süt": IMG_SUT,
            "Sıvı Yağlar": IMG_YAG,
            "Toz Şeker": IMG_SEKER,
            "Tıraş Ürünleri": IMG_TRAŞ,
            "Un": IMG_UN,
            "Yumuşatıcılar": IMG_CAMASIR,
            "Çamaşır Deterjanı": IMG_CAMASIR,
            "Çamaşır Yıkama Ürünleri": IMG_CAMASIR,
            "Çay": IMG_CAY,
            "Çikolata": IMG_CIKOLATA,
            # [BURAYI EKLEDİM] Ekmek için map
            "Ekmek": IMG_EKMEK,
            "Ekmekler": IMG_EKMEK,
            "Unlu Mamüller": IMG_EKMEK  # Eğer veritabanında bu isimle geçiyorsa
        }

        print("Kategorilere göre kesin güncelleme başlıyor...")
        print("-" * 40)

        total_updated = 0

        for cat_name, img_url in category_map.items():
            sql = """
                UPDATE product
                SET image_url = %s
                FROM category
                WHERE product.categoryid = category.id
                AND category.name = %s
            """
            cur.execute(sql, (img_url, cat_name))

            if cur.rowcount > 0:
                print(f"✅ '{cat_name}' -> {cur.rowcount} ürün güncellendi.")
                total_updated += cur.rowcount
            else:
                print(f"⚠️ '{cat_name}' için eşleşme yok.")

        conn.commit()
        print("-" * 40)
        print(f"🎉 TOPLAM {total_updated} ÜRÜN GÜNCELLENDİ.")

    except Exception as e:
        print(f"❌ Hata: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_images_exact_categories()
