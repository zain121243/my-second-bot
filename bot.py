import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ✅ التوكن
TOKEN = os.getenv("token")

if not TOKEN or TOKEN == "token":
    raise ValueError("❌ التوكن غلط! حطه في Railway Variables باسم token")

user_links = {}

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 ارسل رابط الفيديو")

# استقبال الرابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("❌ رابط غير صحيح")
        return

    user_links[user_id] = url

    keyboard = [
        [InlineKeyboardButton("🎥 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت MP3", callback_data="audio")]
    ]

    await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(keyboard))

# 🔥 تحميل بدون تعليق
async def download_async(url, mode):

    def run():
        ydl_opts = {
            'outtmpl': 'file.%(ext)s',
            'quiet': True,
            'noplaylist': True,
        }

        if mode == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            })
        else:
            ydl_opts.update({
                'format': 'best'
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if mode == "audio":
                return os.path.splitext(filename)[0] + ".mp3"
            return filename

    return await asyncio.to_thread(run)

# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    mode = query.data
    url = user_links.get(user_id)

    if not url:
        await context.bot.send_message(user_id, "❌ ارسل الرابط أولاً")
        return

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        file_path = await download_async(url, mode)

        if mode == "audio":
            await context.bot.send_audio(user_id, audio=open(file_path, 'rb'))
        else:
            await context.bot.send_video(user_id, video=open(file_path, 'rb'))

        os.remove(file_path)

    except Exception as e:
        await context.bot.send_message(user_id, f"❌ خطأ:\n{e}")

# تشغيل
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(buttons))

print("Bot running...")
app.run_polling()
