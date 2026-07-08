# 🤖 İş Bildiriş Botu — Qurulum

## 1. Lazımlı proqramları yüklə

```bash
pip install python-telegram-bot requests beautifulsoup4 schedule
```

## 2. Telegram Bot Token al

1. Telegram-da **@BotFather**-a yaz
2. `/newbot` yaz
3. Bot adı ver (məs: `IshBildirish`)
4. Token alacaqsan — `bot.py` faylında `BOT_TOKEN = "..."` yerinə yaz

## 3. Botu işə sal

```bash
python bot.py
```

## 4. Test et

Telegram-da botunu tap, `/start` yaz

## Fayl strukturu

```
scraper.py    → boss.az-dan elan çəkir
bot.py        → Telegram bot (əsas fayl)
jobs.json     → Saxlanılan elanlar (avtomatik yaranır)
users.json    → İstifadəçi məlumatları (avtomatik yaranır)
```

## Bot komandaları

| Komanda | Nə edir |
|---|---|
| /start | Başlanğıc |
| /kateqoriya | Sahə seç |
| /keyword mühasib | Açar söz əlavə et |
| /keyword_sil mühasib | Açar söz sil |
| /status | Ayarlarına bax |
| /test | İndi elanları yoxla |

## Premium sistemi əlavə etmək (sonra)

`users.json`-da istifadəçinin `plan` sahəsini `"premium"` et:

```json
{
  "123456789": {
    "plan": "premium",
    "categories": ["it"],
    "keywords": []
  }
}
```

Ödəniş alan kimi əl ilə aktivləşdirirsən — ilk 50 müştəriyə qədər bu yetər.
