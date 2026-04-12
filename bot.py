import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

user_links = {}
users = set()
download_count = 0

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Stable Video Downloader\n\nSend YouTube or Instagram link 😎")

# HANDLE LINK
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.effective_user.id] = url
    users.add(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("🎬 Video", callback_data="video")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio")]
    ]

    await update.message.reply_text("Choose format 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# YOUTUBE OPTIONS BUILDER
def get_ydl_opts(fmt, use_cookies=False):
    opts = {
        'format': fmt,
        'outtmpl': 'file.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'retries': 10,
        'fragment_retries': 10,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    if use_cookies:
        opts['cookiefile'] = 'cookies.txt'

    return opts

# BUTTON HANDLER
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global download_count

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_links.get(user_id)

    is_instagram = "instagram.com" in url

    # QUALITY OPTIONS (YouTube only)
    if query.data == "video" and not is_instagram:
        keyboard = [
            [InlineKeyboardButton("360p", callback_data="360")],
            [InlineKeyboardButton("720p", callback_data="720")],
            [InlineKeyboardButton("Best", callback_data="best")]
        ]
        await query.message.reply_text("Select quality 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    download_count += 1
    await query.message.reply_text("⏳ Downloading...")

    try:
        # INSTAGRAM (basic)
        if is_instagram:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'file.%(ext)s',
                'noplaylist': True,
                'retries': 5,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

        else:
            # YOUTUBE (multi-layer system)
            if query.data == "360":
                fmt = "best[height<=360]/best"
            elif query.data == "720":
                fmt = "best[height<=720]/best"
            elif query.data == "best":
                fmt = "best"
            elif query.data == "audio":
                fmt = "bestaudio/best"

            success = False

            # 1️⃣ Try normal
            try:
                with yt_dlp.YoutubeDL(get_ydl_opts(fmt)) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                success = True
            except:
                pass

            # 2️⃣ Retry with cookies
            if not success:
                try:
                    with yt_dlp.YoutubeDL(get_ydl_opts(fmt, use_cookies=True)) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)
                    success = True
                except:
                    pass

            # 3️⃣ Fail
            if not success:
                await query.message.reply_text("❌ This video is protected by YouTube.\nTry another video.")
                return

        # AUDIO FIX
        if query.data == "audio":
            filename = filename.rsplit(".", 1)[0] + ".mp3"

        await query.message.reply_text("📤 Uploading...")

        with open(filename, 'rb') as f:
            if query.data == "audio":
                await query.message.reply_audio(
                    f,
                    caption="🚀 Downloaded by Bot\n🔥 Follow @lgd.efx on IG"
                )
            else:
                await query.message.reply_video(
                    f,
                    caption="🚀 Downloaded by Bot\n🔥 Follow @lgd.efx on IG"
                )

        os.remove(filename)

    except Exception:
        if is_instagram:
            await query.message.reply_text("❌ Instagram blocked this reel.")
        else:
            await query.message.reply_text("❌ Download failed. Try another link.")

# STATS
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Stats\n👤 Users: {len(users)}\n📥 Downloads: {download_count}"
    )

# APP START
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
