import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("token")
CHANNEL = "@jbt_313"

user_links = {}

# بدء
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
        [InlineKeyboardButton("🎥 360p", callback_data="360"),
         InlineKeyboardButton("🎥 720p", callback_data="720")],
        [InlineKeyboardButton("🎥 1080p", callback_data="1080")],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")]
    ]

    await update.message.reply_text("اختر الجودة:", reply_markup=InlineKeyboardMarkup(keyboard))

# تحميل
def download(url, mode):

    ydl_opts = {
        'outtmpl': 'file.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }

    # 🎧 صوت
    if mode == "audio":
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        })

    # 🎥 فيديو (ثابت بدون مشاكل)
    else:
        ydl_opts.update({
            'format': 'best'
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if mode == "audio":
            return os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        else:
            return ydl.prepare_filename(info)

# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    mode = query.data
    url = user_links.get(user_id)

    if not url:
        await context.bot.send_message(user_id, "❌ ارسل الرابط اولاً")
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
