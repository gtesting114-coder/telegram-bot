import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

user_links = {}
users = set()
download_count = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 The Ultimate Video Downloader\n\nSend me a video link 😎")

# STEP 1: HANDLE LINK
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.effective_user.id] = url
    users.add(update.effective_user.id)

    if "pinterest.com" in url:
        keyboard = [[InlineKeyboardButton("📌 Download", callback_data="best")]]
    else:
        keyboard = [
            [InlineKeyboardButton("🎬 Video", callback_data="video")],
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio")]
        ]

    await update.message.reply_text("Choose format 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# STEP 2: BUTTON HANDLER
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global download_count

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_links.get(user_id)

    is_pinterest = "pinterest.com" in url
    is_instagram = "instagram.com" in url

    # QUALITY OPTIONS
    if query.data == "video" and not is_pinterest and not is_instagram:
        keyboard = [
            [InlineKeyboardButton("360p", callback_data="360")],
            [InlineKeyboardButton("720p", callback_data="720")],
            [InlineKeyboardButton("1080p", callback_data="1080")],
            [InlineKeyboardButton("Best", callback_data="best")]
        ]
        await query.message.reply_text("Select quality 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    download_count += 1

    await query.message.reply_text("🔍 Fetching video info...")

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title", "Unknown")
        thumbnail = info.get("thumbnail")
        filesize = info.get("filesize") or info.get("filesize_approx")

        if filesize:
            size_mb = round(filesize / (1024 * 1024), 2)
            size_text = f"{size_mb} MB"
        else:
            size_text = "Unknown"

        caption_preview = f"🎬 {title}\n📦 Size: {size_text}"

        if thumbnail:
            await query.message.reply_photo(photo=thumbnail, caption=caption_preview)
        else:
            await query.message.reply_text(caption_preview)

        await query.message.reply_text("⏳ Downloading...")

        # FORMAT HANDLING
        if is_pinterest:
            ydl_opts = {
                'outtmpl': 'file.%(ext)s'
            }

        elif is_instagram:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'file.%(ext)s',
                'noplaylist': True,
                'retries': 10,
                'fragment_retries': 10,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
                }
            }

        else:
            if query.data == "360":
                fmt = "best[height<=360]/best"
            elif query.data == "720":
                fmt = "best[height<=720]/best"
            elif query.data == "1080":
                fmt = "best[height<=1080]/best"
            elif query.data == "best":
                fmt = "best"
            elif query.data == "audio":
                fmt = "bestaudio/best"

            ydl_opts = {
                'format': fmt,
                'outtmpl': 'file.%(ext)s',
                'noplaylist': True
            }

            if query.data == "audio":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

        await query.message.reply_text("⚙️ Processing...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

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

    except Exception as e:
        if is_instagram:
            await query.message.reply_text("❌ Instagram blocked this link. Try another reel.")
        else:
            await query.message.reply_text(f"❌ Error: {str(e)}")

# STATS COMMAND
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Bot Stats\n\n👤 Users: {len(users)}\n📥 Downloads: {download_count}"
    )

# APP START
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
