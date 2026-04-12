import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 sugunan The Ultimate Video Downloader\n\nSend me a video link 😎")

# STEP 1: User sends link
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.effective_user.id] = url

    if "pinterest.com" in url:
        keyboard = [
            [InlineKeyboardButton("📌 Download", callback_data="best")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎬 Video", callback_data="video")],
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio")]
        ]

    await update.message.reply_text(
        "Choose format 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# STEP 2: Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_links.get(user_id)

    is_pinterest = "pinterest.com" in url

    # Show quality options
    if query.data == "video" and not is_pinterest:
        keyboard = [
            [InlineKeyboardButton("360p", callback_data="360")],
            [InlineKeyboardButton("720p", callback_data="720")],
            [InlineKeyboardButton("1080p", callback_data="1080")],
            [InlineKeyboardButton("Best", callback_data="best")]
        ]
        await query.message.reply_text(
            "Select quality 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await query.message.reply_text("🔍 Fetching video info...")

    try:
        # Get info
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

        # FORMAT (NO FFMPEG REQUIRED)
        if is_pinterest:
            fmt = "best"
        elif query.data == "360":
            fmt = "best[height<=360][ext=mp4]/best"
        elif query.data == "720":
            fmt = "best[height<=720][ext=mp4]/best"
        elif query.data == "1080":
            fmt = "best[height<=1080][ext=mp4]/best"
        elif query.data == "best":
            fmt = "best[ext=mp4]/best"
        elif query.data == "audio":
            fmt = "bestaudio/best"

        ydl_opts = {
            'format': fmt,
            'outtmpl': 'file.%(ext)s',
            'noplaylist': True
        }

        # Audio conversion (may fail without ffmpeg, but safe fallback)
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
        await query.message.reply_text(f"❌ Error: {str(e)}")

# APP START
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
