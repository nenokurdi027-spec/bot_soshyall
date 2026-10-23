# ============================================================
#  Telegram Multi-Platform Video Downloader Bot
#  Single-file edition. No external modules of our own.
#  Supports: TikTok, Instagram (reels/posts/stories), Snapchat,
#            Facebook, Pinterest, Telegram, YouTube.
# ============================================================
import os
import re
import uuid
import logging
import asyncio
import subprocess

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# ---------------------- CONFIG ----------------------
BOT_TOKEN        = os.getenv("BOT_TOKEN", "").strip()
DOWNLOAD_DIR     = os.getenv("DOWNLOAD_DIR", "downloads")
MAX_FILESIZE_MB  = int(os.getenv("MAX_FILESIZE_MB", "50"))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "240"))

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bot")

# ---------------------- PLATFORM DETECT ----------------------
PLATFORM_PATTERNS = {
    "tiktok":    [r"tiktok\.com", r"vt\.tiktok\.com"],
    "instagram": [r"instagram\.com", r"instagr\.am"],
    "snapchat":  [r"snapchat\.com"],
    "facebook":  [r"facebook\.com", r"fb\.watch"],
    "pinterest": [r"pinterest\.", r"pin\.it"],
    "telegram":  [r"t\.me"],
    "youtube":   [r"youtube\.com", r"youtu\.be"],
}

def detect_platform(url: str) -> str:
    for name, patterns in PLATFORM_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, url, re.IGNORECASE):
                return name
    return "generic"

# ---------------------- SUBPROCESS HELPERS ----------------------
def _run_blocking(cmd: list, timeout: int):
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except FileNotFoundError as e:
        return -2, "", f"missing binary: {e}"
    except Exception as e:
        return -3, "", f"sub _process error: {e}"

async def _run(cmd: list, timeout: int = DOWNLOAD_TIMEOUT):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_blocking, cmd, timeout)

# ---------------------- DOWNLOAD ENGINES ----------------------
async def download_with_ytdlp(url: str, platform: str):
    out_id   = uuid.uuid4().hex
    template = os.path.join(DOWNLOAD_DIR, f"{out_id}_%(title).80s.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--restrict-filenames",
        "--no-part",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", template,
        url,
    ]
    if platform in ("facebook", "pinterest"):
        cmd += ["--add-header", "User-Agent:Mozilla/5.0"]
    rc, out, err = awaitrun(cmd)
    if rc != 0:
        log.warning("yt-dlp failed (%s): %s", rc, err[-400:])
        return None
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(out_id):
            return os.path.join(DOWNLOAD_DIR, f)
    return None

async def download_with_gallerydl(url: str):
    out_id = uuid.uuid4().hex
    dest   = os.path.join(DOWNLOAD_DIR, out_id)
    os.makedirs(dest, exist_ok=True)
    cmd = ["gallery-dl", "-D", dest, url]
    rc, out, err = await _run(cmd)
    if rc != 0:
        log.warning("gallery-dl failed (%s): %s", rc, err[-400:])
        return None
    video_exts = (".mp4", ".mkv", ".webm", ".mov", ".m4v")
    found = []
    for f in os.listdir(dest):
        full = os.path.join(dest, f)
        if os.path.isfile(full):
            found.append(full)
    for f in found:
        if f.lower().endswith(video_exts):
            return f
    return found[0] if found else None

async def smart_download(url: str):
    platform = detect_platform(url)
    if platform in ("snapchat", "instagram", "pinterest"):
        f = await download_with_gallerydl(url)
        if f:
            return f, platform
    f = await download_with_ytdlp(url, platform)
    if f:
        return f, platform
    f = await download_with_gallerydl(url)
    return f, platform

# ---------------------- CLEANUP ----------------------
def cleanup(path: str):
    try:
        if path and os.path.isfile(path):
            os.remove(path)
            parent = os.path.dirname(path)
            if parent and os.path.abspath(parent) != os.path.abspath(DOWNLOAD_DIR):
                try: os.rmdir(parent)
                except OSError: pass
    except Exception:
        pass

# ---------------------- UI TEXT ----------------------
WELCOME = (
    "🦅 *بەخێربێی بۆ بۆتی دابەز چاندنی ڤیدیۆ*\n\n"
    "تەنها لینکێک بنێرە و من ڤیدیۆکەت بۆ دەگرم.\n\n"
    "📥 *پلاتفۆرمەکانی پشتگیری‌کراو:*\n"
    "• تیک‌تۆک\n"
    "• ئینستاگرام (ستۆری و پۆست)\n"
    "• سناپ‌چات (ستۆری)\n"
    "• فەیسبووک\n"
    "• پینترێست\n"
    "• تیلیگرام (ستۆری و ڤیدیۆ)\n"
    "• یوتیوب\n\n"
    "⚡ کواڵێتی بەرزترین — خێراترین — بێ سنوور"
)

HELP = (
    "🧭 *چۆن بەکاربهێنم:*\n\n"
    "1️⃣ لینکی ڤیدیۆکە کۆپی بکە\n"
    "2️⃣ لێرە بینێرە\n"
    "3️⃣ چاوەڕێ بکە — من ڤیدیۆکەت بۆ دەنێرم\n\n"
    "💡 نموونە:\n"
    "`https://www.tiktok.com/@user/video/123...`\n"
    "`https://www.instagram.com/reel/abc...`"
)

PLATFORMS_TEXT = (
    "🌐 *پلاتفۆرمەکانی پشتگیری‌کراو*\n\n"
    "✅ تیک‌تۆک (ڤیدیۆ + ستۆری)\n"
    "✅ ئینستاگرام (ڕیل، پۆست، ستۆری)\n"
    "✅ سناپ‌چات (ستۆری)\n"
    "✅ فەیسبووک (ڤیدیۆ + ستۆری)\n"
    "✅ پینترێست (ڤیدیۆ)\n"
    "✅ تیلیگرام (ستۆری + ڤیدیۆ)\n"
    "✅ یوتیوب\n\n"
    "🔗 تەنها لینکەکە بنێرە."
)

STATS_TEXT = (
    "📊 *بۆت ئامادەیە*\n\n"
    "🟢 سێرڤەر:الاک\n"
    "⚡ خێرایی: باش\n"
    "💾 کواڵێتی: بەرزترین"
)

def main_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton("📥 چۆن بەکاربهێنم", callback_data="help")],
        [InlineKeyboardButton("⚡ پلاتفۆرمەکان",   callback_data="platforms")],
        [InlineKeyboardButton("📊 ستاتیستیک",       callback_data="stats")],
    ]
    return InlineKeyboardMarkup(kb)

# ---------------------- HANDLERS ----------------------
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME, parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(),
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP, parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(),
    )

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except Exception:
        pass
    if q.data == "help":
        await q.edit_message_text(HELP, parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=main_keyboard())
    elif q.data == "platforms":
        await q.edit_message_text(PLATFORMS_TEXT, parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=main_keyboard())
    elif q.data == "stats":
        await q.edit_message_text(STATS_TEXT, parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=main_keyboard())

async def on_url(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    url = update.message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text(
            "⚠️ تکایە لینکێکی دروست بنێرە (دەست پێبکات بە http/https)."
        )
        return

    status = await update.message.reply_text(
        "⏳ *داگرتن دەستیپێکرد...*", parse_mode=ParseMode.MARKDOWN
    )

    try:
        await ctx.bot.send_chat_action(
            update.effective_chat.id, ChatAction.UPLOAD_VIDEO
        )
    except Exception:
        pass

    filepath = None
    try:
        filepath, platform = await smart_download(url)
    except Exception as e:
        log.exception("download failed")
        await status.edit_text(
            f"❌ هەڵە لە داگرتن: `{e}`", parse_mode=ParseMode.MARKDOWN
        )
        return

    if not filepath or not os.path.isfile(filepath):
        await status.edit_text(
            "❌ نەتوانرا ڤیدیۆکە دابەزێنم.\n"
            "💡 دڵنیابە لینکەکە کراوەتەوە و ڤیدیۆیەکەی تێدایە.\n"
            "🔒 ئەگەر ئەکاونتەکە تایبەتە، پێویستە کوکیز هەبێت."
        )
        cleanup(filepath)
        return

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if size_mb > MAX_FILESIZE_MB:
        await status.edit_text(
            f"⚠️ ڤیدیۆکە زۆر گەورەیە ({size_mb:.1f} MB).\n"
            f"سنووری ناردن {MAX_FILESIZE_MB} MB."
        )
        cleanup(filepath)
        return

    try:
        with open(filepath, "rb") as f:
            await update.message.reply_video(
                video=f,
                caption=(
                    f"✅ *دابەزێندرا* — {platform.upper()}\n"
                    f"📦 {size_mb:.1f} MB"
                ),
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
            )
        try:
            await status.delete()
        except Exception:
            pass
    except Exception as e:
        log.exception("upload failed")
        await status.edit_text(
            f"❌ هەڵە لە ناردن: `{e}`", parse_mode=ParseMode.MARKDOWN
        )
    finally:
        cleanup(filepath)

# ---------------------- MAIN ----------------------
def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "❌ BOT_TOKEN دانەنراوە.\n"
            "   environment variable `BOT_TOKEN` دابنێ."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_url))

    log.info("bot online — talons sharp")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
