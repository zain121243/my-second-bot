import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("token")

user_links = {}

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 ارسل الرابط")

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
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")]
    ]

    await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(keyboard))

# تحميل
def download(url, mode):
    ydl_opts = {
        'outtmpl': 'file.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }

    if mode == "audio":
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        })
    else:
        # 🔥 بدون أي فورمات (هذا السر)
        pass

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if mode == "audio":
            return os.path.splitext(filename)[0] + ".mp3"
        else:
            return filename

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
        file_path = download(url, mode)

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
