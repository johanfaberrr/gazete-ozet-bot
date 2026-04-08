import os
import requests
import openai
from datetime import datetime
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()

# API Anahtarları
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# OpenAI ayarı
openai.api_key = OPENAI_API_KEY

def get_gazete_content():
    """Resmi Gazete'den bugünün içeriğini çek"""
    try:
        url = "https://www.resmigazete.gov.tr"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ana içerik bölümünü bul
        content = soup.find('div', class_=['content', 'main', 'body'])
        
        if content:
            text = content.get_text(separator=' ', strip=True)[:2000]
        else:
            text = soup.get_text(separator=' ', strip=True)[:2000]
        
        return text if text else "Gazete içeriği alınamadı"
    
    except Exception as e:
        print(f"Hata: {e}")
        return f"Gazete çekilirken hata oluştu: {str(e)}"

def summarize_with_openai(text):
    """OpenAI ile metni özetle"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Sen Resmi Gazete haberlerini Türkçe olarak özetleyen bir yardımcısın. Kısa, öz ve anlaşılır özetler hazırla."
                },
                {
                    "role": "user",
                    "content": f"Lütfen bu metni 2-3 paragrafta özetle:\n\n{text}"
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"OpenAI Hatası: {e}")
        return "Özet oluşturulamadı"

def send_telegram_message(message):
    """Telegram'a mesaj gönder"""
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
    """Ana fonksiyon"""
    print("🚀 Gazete Özet Bot Başlatılıyor...")
    print(f"⏰ Saat: {datetime.now()}")
    
    # Gazete içeriğini çek
    print("📰 Gazete içeriği çekiliyor...")
    gazete_text = get_gazete_content()
    print(f"✅ İçerik çekildi ({len(gazete_text)} karakter)")
    
    # OpenAI ile özetle
    print("🤖 OpenAI ile özet oluşturuluyor...")
    ozet = summarize_with_openai(gazete_text)
    print("✅ Özet oluşturuldu")
    
    # Telegram mesajı hazırla
    tarih = datetime.now().strftime("%d.%m.%Y")
    telegram_message = f"""
📰 <b>Resmi Gazete Günlük Özeti</b>
📅 Tarih: {tarih}

<b>Özet:</b>
{ozet}

🔗 Kaynak: https://www.resmigazete.gov.tr
"""
    
    # Telegram'a gönder
    print("📤 Telegram'a gönderiliyor...")
    send_telegram_message(telegram_message)
    
    print("✅ İşlem tamamlandı!")

if __name__ == "__main__":
    main()
