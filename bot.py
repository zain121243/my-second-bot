import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("token")
CHANNEL = "@jbt_313"
COOKIE_FILE = "www.youtube.com_cookies.txt"

if not TOKEN:
    raise ValueError("❌ حط التوكن بمتغير البيئة باسم token")

user_links = {}
last_request_time = {}

async def check_join(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_join(user_id, context.bot):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك", url=f"https://t.me/{CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ تحقق", callback_data="check")]
        ]
        await update.message.reply_text("🔒 اشترك بالقناة أولاً", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("📥 ارسل الرابط")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_join(user_id, context.bot):
        await update.message.reply_text("🔒 اشترك أولاً")
        return

    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ رابط غير صحيح")
        return

    user_links[user_id] = url

    keyboard = [
        [InlineKeyboardButton("🎥 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")]
    ]

    await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(keyboard))

def download_video(url, mode):

    ydl_opts = {
        'outtmpl': 'file.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'cookiefile': COOKIE_FILE,
    }

    if mode == "audio":
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        })

    # 🔥 ملاحظة: ماكو format للفيديو نهائيًا

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if mode == "audio":
            return os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        else:
            return ydl.prepare_filename(info)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    mode = query.data
    url = user_links.get(user_id)

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        file_path = download_video(url, mode)

        if mode == "audio":
            await context.bot.send_audio(user_id, audio=open(file_path, 'rb'))
        else:
            await context.bot.send_video(user_id, video=open(file_path, 'rb'))

        os.remove(file_path)

    except Exception as e:
        await context.bot.send_message(user_id, f"❌ خطأ:\n{e}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")
app.run_polling()
