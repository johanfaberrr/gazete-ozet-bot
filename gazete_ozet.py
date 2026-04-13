import os
import requests
import anthropic
from datetime import datetime
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_html(url):
    """URL'den HTML çeker, encoding'i otomatik tespit eder."""
    r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
    r.raise_for_status()
    # encoding'i zorla atama — HTML'deki meta tagından otomatik tespit et
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup

def get_links_from_anasayfa(tarih):
    print("DEBUG: Ana sayfa deneniyor...")
    soup = fetch_html("https://www.resmigazete.gov.tr")
    links = [
        a['href'] for a in soup.find_all('a', href=True)
        if a['href'].endswith('.htm') and tarih in a['href']
        and 'ilanlar' not in a['href']  # ilan sayfalarını filtrele
    ]
    print(f"DEBUG: Ana sayfadan {len(links)} link bulundu")
    return links

def get_links_from_fihrist(tarih, yil, ay):
    fihrist_url = f"https://www.resmigazete.gov.tr/eskiler/{yil}/{ay}/{tarih}.htm"
    print(f"DEBUG: Arşiv deneniyor: {fihrist_url}")
    soup = fetch_html(fihrist_url)
    links = [
        a['href'] for a in soup.find_all('a', href=True)
        if a['href'].endswith('.htm') and tarih in a['href']
        and 'ilanlar' not in a['href']
    ]
    # Relative linkleri absolute yap
    links = [
        l if l.startswith('http') else f"https://www.resmigazete.gov.tr{l}"
        for l in links
    ]
    print(f"DEBUG: Arşivden {len(links)} link bulundu")
    return links

def get_gazete_content():
    try:
        tarih = datetime.now().strftime("%Y%m%d")
        yil = datetime.now().strftime("%Y")
        ay = datetime.now().strftime("%m")

        try:
            links = get_links_from_anasayfa(tarih)
        except Exception as e:
            print(f"DEBUG: Ana sayfa hatası: {e}")
            links = []

        if not links:
            try:
                links = get_links_from_fihrist(tarih, yil, ay)
            except Exception as e:
                print(f"DEBUG: Arşiv hatası: {e}")
                return None

        if not links:
            print("DEBUG: Hiç link bulunamadı")
            return None

        all_text = []
        for url in links[:5]:
            if not url.startswith('http'):
                url = f"https://www.resmigazete.gov.tr{url}"
            try:
                soup = fetch_html(url)
                # Gereksiz HTML elementlerini temizle
                for tag in soup(['script', 'style', 'head']):
                    tag.decompose()
                text = soup.get_text(separator=' ', strip=True)
                # Tekrarlayan boşlukları temizle
                import re
                text = re.sub(r'\s+', ' ', text).strip()
                print(f"DEBUG: Makale uzunluğu: {len(text)} karakter")
                all_text.append(text[:2000])  # 800 → 2000 karakter
            except Exception as e:
                print(f"DEBUG: Makale hatası ({url}): {e}")
                continue

        return '\n\n---\n\n'.join(all_text) if all_text else None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

def summarize_with_claude(text):
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,  # 300 → 1024
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Aşağıdaki Resmi Gazete metinlerini Türkçe olarak 3-4 paragrafta özetle. "
                        "Her paragraf farklı bir konuyu (yönetmelik, tebliğ, karar vb.) ele alsın. "
                        "Sade ve anlaşılır bir dil kullan.\n\n"
                        f"{text}"
                    )
                }
            ]
        )
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
        # Telegram mesaj limiti 4096 karakter
        if len(message) > 4096:
            message = message[:4090] + "..."
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Telegram mesajı gönderildi!")
            return True
        else:
            print(f"❌ Telegram hatası: {response.text}")
            return False
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")
        return False

def main():
    print("🚀 Gazete Özet Botu Başlıyor...")
    print(f"⏰ Zaman: {datetime.now()}")

    print("📰 Gazete içeriği alınıyor...")
    gazete_text = get_gazete_content()

    tarih = datetime.now().strftime("%d.%m.%Y")

    if not gazete_text:
        print("❌ İçerik alınamadı, hata mesajı gönderiliyor...")
        telegram_message = (
            f"📰 <b>Resmi Gazete Günlük Özeti</b>\n\n"
            f"📅 Tarih: {tarih}\n\n"
            f"⚠️ Bugün Resmi Gazete içeriği alınamadı. Site erişilemez durumda olabilir.\n\n"
            f"🔗 Manuel kontrol: https://www.resmigazete.gov.tr"
        )
        send_telegram_message(telegram_message)
        return

    print(f"✅ İçerik alındı ({len(gazete_text)} karakter)")

    print("🤖 Claude ile özet oluşturuluyor...")
    ozet = summarize_with_claude(gazete_text)
    print("✅ Özet oluşturuldu")

    telegram_message = (
        f"📰 <b>Resmi Gazete Günlük Özeti</b>\n\n"
        f"📅 Tarih: {tarih}\n\n"
        f"<b>Özet:</b>\n\n"
        f"{ozet}\n\n"
        f"🔗 Kaynak: https://www.resmigazete.gov.tr"
    )

    print("📤 Telegram'a gönderiliyor...")
    send_telegram_message(telegram_message)
    print("✅ İşlem tamamlandı!")

if __name__ == "__main__":
    main()
