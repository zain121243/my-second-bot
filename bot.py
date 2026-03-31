import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("token")

user_links = {}

# 🌟 رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ ياعلي مدد ✨\n\n"
        "🤖 بوت تحميل الفيديوهات\n"
        "يدعم:\n"
        "YouTube | TikTok | Instagram | Twitter | Facebook\n\n"
        "📥 ارسل الرابط الآن"
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
        "📊 اختر الجودة:\nياعلي مدد ✨",
        reply_markup=reply_markup
    )

# ⬇️ تحميل الفيديو (🔥 نسخة قوية بدون cookies)
def download_video(url, quality):

    ydl_opts = {
        'outtmpl': 'download.%(ext)s',
        'quiet': True,
        'noplaylist': True,

        # 🔥 حل مشكلة يوتيوب
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },

        'http_headers': {
            'User-Agent': 'com.google.android.youtube/17.31.35'
        },

        'geo_bypass': True,
    }

    if quality == "audio":
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        })
    else:
        ydl_opts.update({
            'format': f'bestvideo[height<={quality}]+bestaudio/best'
        })

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
        "انتظر قليلاً جاري التحميل 📥"
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

        os.remove(file_path)

    except Exception as e:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ صار خطأ:\n{e}"
        )

# 🚀 تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")

app.run_polling()
