import os
import requests
import anthropic
import cloudscraper
from datetime import datetime
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

scraper = cloudscraper.create_scraper()

# API Anahtarları
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_links_from_anasayfa(tarih, headers):
    """Ana sayfadan günün makale linklerini çek."""
    print("DEBUG: Ana sayfa deneniyor...")
    response = scraper.get("https://www.resmigazete.gov.tr", headers=headers, timeout=15, verify=False)
    print(f"DEBUG ana sayfa status: {response.status_code}")
    if response.status_code != 200:
        return []
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [
        a['href'] for a in soup.find_all('a', href=True)
        if a['href'].endswith('.htm') and tarih in a['href']
    ]
    print(f"DEBUG ana sayfadan {len(links)} link bulundu")
    return links

def get_links_from_fihrist(tarih, yil, ay, headers):
    """Fihrist sayfasından günün makale linklerini çek."""
    fihrist_url = f"https://www.resmigazete.gov.tr/eskiler/{yil}/{ay}/{tarih}.htm"
    print(f"DEBUG: Fihrist deneniyor: {fihrist_url}")
    response = scraper.get(fihrist_url, headers=headers, timeout=15, verify=False)
    print(f"DEBUG fihrist status: {response.status_code}")
    if response.status_code != 200:
        return []
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [
        a['href'] for a in soup.find_all('a', href=True)
        if a['href'].endswith('.htm') and tarih in a['href']
    ]
    print(f"DEBUG fihristden {len(links)} link bulundu")
    return links

def get_gazete_content():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        tarih = datetime.now().strftime("%Y%m%d")
        yil = datetime.now().strftime("%Y")
        ay = datetime.now().strftime("%m")

        # Önce ana sayfadan dene, olmazsa fihrist sayfasından dene
        links = get_links_from_anasayfa(tarih, headers)
        if not links:
            links = get_links_from_fihrist(tarih, yil, ay, headers)

        if not links:
            print("DEBUG: Hiçbir kaynaktan link alınamadı")
            return None

        # İlk 5 makaleyi çek
        all_text = []
        for url in links[:5]:
            if not url.startswith('http'):
                url = f"https://www.resmigazete.gov.tr{url}"
            try:
                r = scraper.get(url, headers=headers, timeout=15, verify=False)
                r.encoding = 'utf-8'
                s = BeautifulSoup(r.content, 'html.parser')
                text = s.get_text(separator=' ', strip=True)
                print(f"DEBUG makale uzunluk: {len(text)}")
                all_text.append(text[:800])
            except Exception as e:
                print(f"DEBUG makale hata: {e}")
                continue
        return '\n\n'.join(all_text) if all_text else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEBUG hata: {str(e)}")
        return None

def summarize_with_claude(text):
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"Sen Resmi Gazete haberlerini Türkçe olarak özetleyen bir yardımcısın. Kısa, öz ve anlaşılır özetler hazırla.\n\nLütfen bu metni 2-3 paragrafta özetle:\n\n{text}"
                }
            ]
        )
        print(f"DEBUG response type: {type(message.content)}")
        print(f"DEBUG response: {message.content}")
        if isinstance(message.content, list):
            return message.content[0].text
        return str(message.content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Özet oluşturulamadı: {str(e)}"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Telegram mesajı başarıyla gönderildi!")
            return True
        else:
            print(f"❌ Telegram hatası: {response.text}")
            return False
    except Exception as e:
        print(f"Telegram Gönderme Hatası: {e}")
        return False

def main():
    print("🚀 Gazete Özet Bot Başlatılıyor...")
    print(f"⏰ Saat: {datetime.now()}")

    print("📰 Gazete içeriği çekiliyor...")
    gazete_text = get_gazete_content()

    tarih = datetime.now().strftime("%d.%m.%Y")

    if not gazete_text:
        print("❌ Gazete içeriği alınamadı, hata mesajı gönderiliyor...")
        telegram_message = f"""📰 <b>Resmi Gazete Günlük Özeti</b>
📅 Tarih: {tarih}

⚠️ Bugün Resmi Gazete içeriği alınamadı. Site erişilemez durumda olabilir.

🔗 Manuel kontrol: https://www.resmigazete.gov.tr"""
        send_telegram_message(telegram_message)
        return

    print(f"✅ İçerik çekildi ({len(gazete_text)} karakter)")
    print(f"DEBUG içerik: {gazete_text[:200]}")

    print("🤖 Claude ile özet oluşturuluyor...")
    ozet = summarize_with_claude(gazete_text)
    print("✅ Özet oluşturuldu")

    telegram_message = f"""📰 <b>Resmi Gazete Günlük Özeti</b>
📅 Tarih: {tarih}

<b>Özet:</b>
{ozet}

🔗 Kaynak: https://www.resmigazete.gov.tr"""

    print("📤 Telegram'a gönderiliyor...")
    send_telegram_message(telegram_message)
    print("✅ İşlem tamamlandı!")

if __name__ == "__main__":
    main()
