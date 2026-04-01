import os
import subprocess
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

    user_links[user_id] = url

    keyboard = [
        [InlineKeyboardButton("🎥 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")]
    ]

    await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(keyboard))

# تحميل فعلي (🔥 نفس التيرمنال)
def download(url, mode):

    if mode == "audio":
        cmd = f'yt-dlp -x --audio-format mp3 -o "file.%(ext)s" "{url}"'
    else:
        cmd = f'yt-dlp -o "file.%(ext)s" "{url}"'

    subprocess.run(cmd, shell=True)

    # البحث عن الملف
    for file in os.listdir():
        if file.startswith("file."):
            return file

# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    mode = query.data
    url = user_links.get(user_id)

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
