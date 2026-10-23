# 🦅 Telegram Multi-Platform Video Downloader Bot

بۆتێکی تیلیگرام بۆ دابەزاندنی ڤیدیۆ لە پلاتفۆرمە جیاوازەکان بە کواڵێتی بەرز.

## ✨ پلاتفۆرمەکانی پشتگیری‌کراو

- ✅ تیک‌تۆک (TikTok) — ڤیدیۆ + ستۆری
- ✅ ئینستاگرام (Instagram) — ڕیل، پۆست، ستۆری
- ✅ سناپ‌چات (Snapchat) — ستۆری
- ✅ فەیسبووک (Facebook) — ڤیدیۆ + ستۆری
- ✅ پینترێست (Pinterest) — ڤیدیۆ
- ✅ تیلیگرام (Telegram) — ستۆری + ڤیدیۆ
- ✅ یوتیوب (YouTube)

## 🚀 خێرا دەستپێکردن (Justrunmy.app)

### 1️⃣ دروستکردنی بۆت لە BotFather
- لە Telegram بگەڕێ بۆ **@BotFather**
- `/newbot` بنێرە
- تۆکنەکەت کۆپی بکە

### 2️⃣ بەرزکردنەوە
- فایلەکان ZIP بکە یان ئەم ڕیپۆیە بەکاربهێنە
- لە Justrunmy.app: **Upload ZIP**
- **Start Command**: `bash start.sh`
- **Environment Variables**:
  - `BOT_TOKEN` = تۆکنەکەت لە BotFather
  - `MAX_FILESIZE_MB` = `50`

### 3️⃣ تاقیکردنەوە
- لە Telegram `/start` بنێرە
- لینکێکی ڤیدیۆ بنێرە
- چاوەڕێ بکە — ڤیدیۆکەت دێت ✅

## 🖥️ خۆکار (Local)

```bash
git clone https://github.com/YOUR_USERNAME/telegram-downloader-bot.git
cd telegram-downloader-bot
pip install -r requirements.txt
cp .env.example .env
# .env پڕبکەرەوە بە BOT_TOKEN
python bot.py
```

## 🐳 Docker

```bash
docker build -t tg-downloader .
docker run -d --env-file .env --name tg-downloader tg-downloader
```

## 🔧 کێشە باوەکان

| کێشە | چارەسەر |
|------|---------|
| `BOT_TOKEN not set` | لە Env Vars دایبنێ |
| `yt-dlp not found` | `requirements.txt` دڵنیابە |
| ڤیدیۆ نایەت | لینک گشتی بەکاربهێنە یان `cookies.txt` |
| Conflict error | بۆتەکە لە شوێنی تر ڕادەکات، Stop بکە |

## 📝 مۆڵەت

MIT — بە ئازادی بەکاری بهێنە.
