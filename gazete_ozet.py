import os
import requests
import anthropic
from datetime import datetime
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

# API Anahtarları
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_gazete_content():
    try:
        url = "https://www.resmigazete.gov.tr"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', class_=['content', 'main', 'body'])
        if content:
            text = content.get_text(separator=' ', strip=True)[:2000]
        else:
            text = soup.get_text(separator=' ', strip=True)[:2000]
        return text if text else "Gazete içeriği alınamadı"
    except Exception as e:
        return f"Gazete çekilirken hata oluştu: {str(e)}"

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
        return message.content[0].text
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
    print(f"✅ İçerik çekildi ({len(gazete_text)} karakter)")

    print("🤖 Claude ile özet oluşturuluyor...")
    ozet = summarize_with_claude(gazete_text)
    print("✅ Özet oluşturuldu")

    tarih = datetime.now().strftime("%d.%m.%Y")
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
