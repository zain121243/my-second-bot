import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")

user_links = {}

# 🌟 رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ ياعلي مدد ✨\n\n"
        "📥 ارسل رابط الفيديو\n"
        "وسيتم خدمتك بأفضل جودة 🔥"
    )

# 📩 استقبال الرابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.effective_user.id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎥 360p", callback_data="360"),
            InlineKeyboardButton("🎥 720p", callback_data="720"),
        ],
        [
            InlineKeyboardButton("🎥 1080p", callback_data="1080"),
        ],
        [
            InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📊 اختر الجودة المطلوبة:\n"
        "ياعلي مدد ✨",
        reply_markup=reply_markup
    )

# ⬇️ تحميل الفيديو
def download_video(url, quality):
    if quality == "audio":
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'outtmpl': 'video.%(ext)s'
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# 🎯 عند الضغط على زر
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    quality = query.data
    url = user_links.get(user_id)

    await query.edit_message_text(
        "⏳ ياعلي مدد...\n"
        "انتظر قليلاً سيتم تنزيل الفيديو أو الصوت 📥"
    )

    try:
        file_path = download_video(url, quality)

        if quality == "audio":
            await context.bot.send_audio(
                chat_id=user_id,
                audio=open(file_path, 'rb'),
                caption="🎧 تم التحميل بنجاح\nياعلي مدد ✨"
            )
        else:
            await context.bot.send_video(
                chat_id=user_id,
                video=open(file_path, 'rb'),
                caption="🎥 تم التحميل بنجاح\nياعلي مدد ✨"
            )

        # حذف الملف بعد الإرسال (مهم للسيرفر)
        os.remove(file_path)

    except Exception as e:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ حدث خطأ:\n{e}"
        )

# 🚀 تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")

app.run_polling()