import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("token")
CHANNEL = "@jbt_313"

user_links = {}
last_request_time = {}

# 🔒 تحقق الاشتراك
async def check_join(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🌟 start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_join(user_id, context.bot):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك", url=f"https://t.me/{CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ تحقق", callback_data="check")]
        ]
        await update.message.reply_text(
            "🔒 اشترك بالقناة أولاً\nياعلي مدد ✨",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(
        "✨ ياعلي مدد ✨\n\n📥 ارسل الرابط"
    )

# 📩 استقبال الرابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_join(user_id, context.bot):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك", url=f"https://t.me/{CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ تحقق", callback_data="check")]
        ]
        await update.message.reply_text("🔒 اشترك أولاً", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    now = asyncio.get_event_loop().time()
    if user_id in last_request_time and now - last_request_time[user_id] < 5:
        await update.message.reply_text("⏳ انتظر قليلاً")
        return
    last_request_time[user_id] = now

    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ رابط غير صحيح")
        return

    user_links[user_id] = url

    keyboard = [
        [InlineKeyboardButton("🎥 360p", callback_data="360"),
         InlineKeyboardButton("🎥 720p", callback_data="720")],
        [InlineKeyboardButton("🎥 1080p", callback_data="1080")],
        [InlineKeyboardButton("🎧 صوت MP3", callback_data="audio")]
    ]

    await update.message.reply_text(
        "🎬 اختر الجودة\nياعلي مدد ✨",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ⬇️ تحميل
def download_video(url, quality):

    ydl_opts = {
        'outtmpl': 'file.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        }
    }

    if quality == "audio":
        ydl_opts.update({
            'format': 'ba/b',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
    else:
        ydl_opts.update({
            'format': f'bestvideo[height<={quality}]+bestaudio/best'
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if quality == "audio":
            return os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        else:
            return ydl.prepare_filename(info)

# 🎯 الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    quality = query.data
    url = user_links.get(user_id)

    if not url:
        await context.bot.send_message(user_id, "❌ أرسل الرابط أولاً")
        return

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        file_path = download_video(url, quality)

        if quality == "audio":
            await context.bot.send_audio(user_id, audio=open(file_path, 'rb'))
        else:
            await context.bot.send_video(user_id, video=open(file_path, 'rb'))

        os.remove(file_path)

    except Exception as e:
        await context.bot.send_message(user_id, f"❌ خطأ:\n{e}")

# 🚀 تشغيل
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")

app.run_polling()
