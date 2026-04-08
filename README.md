# 📰 Resmi Gazete Özet Bot

Resmi Gazete'nin günlük içeriklerini özetleyip Telegram'a gönderen otomatik bot.

## 🎯 Özellikler

- ✅ Günde bir kez Resmi Gazete'den veri çeker
- ✅ OpenAI GPT ile içeriği özetler
- ✅ Telegram'a özeti gönderir
- ✅ Tamamen otomatik çalışır
- ✅ GitHub Actions ile çalıştırılır

## 🔧 Kurulum

### 1. Gerekli Hesaplar

- **GitHub Hesabı** (Depo için)
- **OpenAI API Key** (https://platform.openai.com/api-keys)
- **Telegram Bot** (@BotFather ile oluşturun)

### 2. GitHub Secrets Ayarı

Depo ayarlarında (`Settings → Secrets and variables → Actions`) şu secret'leri ekleyin:

| Secret | Değer |
|--------|-------|
| `OPENAI_API_KEY` | OpenAI API Key'iniz |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token'ınız |
| `TELEGRAM_CHAT_ID` | Mesajların gönderileceği Chat ID |

### 3. Telegram Chat ID Bulma

1. Botunuza bir mesaj atın
2. Şu URL'ye gidin: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. `