import os
import yt_dlp
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("token")
CHANNEL = "@jbt_313"  # 🔥 غيره إلى قناتك

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
        "✨ ياعلي مدد ✨\n\n"
        "🤖 بوت تحميل الفيديوهات الاحترافي\n\n"
        "📥 ارسل الرابط الآن"
    )

# 📩 استقبال الرابط (🔥 بدون مشاكل يوتيوب)
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
        await update.message.reply_text("❌ ارسل رابط صحيح")
        return

    user_links[user_id] = url

    keyboard = [
        [InlineKeyboardButton("🎥 360p", callback_data="360"),
         InlineKeyboardButton("🎥 720p", callback_data="720")],
        [InlineKeyboardButton("🎥 1080p", callback_data="1080")],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")]
    ]

    # 🔥 إذا يوتيوب → بدون قراءة
    if "youtube.com" in url or "youtu.be" in url:
        await update.message.reply_text(
            "🎬 رابط يوتيوب جاهز\nاختر الجودة\nياعلي مدد ✨",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 🔥 باقي المواقع نحاول نجيب معلومات
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title", "بدون عنوان")
        thumbnail = info.get("thumbnail")

        if thumbnail:
            await update.message.reply_photo(
                photo=thumbnail,
                caption=f"🎬 {title}\nاختر الجودة\nياعلي مدد ✨",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"🎬 {title}\nاختر الجودة\nياعلي مدد ✨",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except:
        await update.message.reply_text(
            "🎬 الرابط جاهز\nاختر الجودة\nياعلي مدد ✨",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ⬇️ تحميل (🔥 يوتيوب API + باقي المواقع yt-dlp)
def download_video(url, quality):

    # 🔥 يوتيوب
    if "youtube.com" in url or "youtu.be" in url:
        api_url = "https://cobalt.tools/api/json"

        data = {
            "url": url,
            "vQuality": quality if quality != "audio" else "max",
            "isAudioOnly": True if quality == "audio" else False
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        res = requests.post(api_url, json=data, headers=headers)
        result = res.json()

        if result.get("status") == "success":
            return result["url"]
        else:
            raise Exception("فشل تحميل من API")

    # 🔥 باقي المواقع
    ydl_opts = {
        'outtmpl': 'file.%(ext)s',
        'quiet': True,
        'noplaylist': True,
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

# 🎯 الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "check":
        if await check_join(user_id, context.bot):
            await query.edit_message_text("✅ تم التحقق، ارسل الرابط الآن")
        else:
            await query.answer("❌ لم تشترك", show_alert=True)
        return

    quality = query.data
    url = user_links.get(user_id)

    await query.edit_message_text("⏳ جاري التحميل... يا علي مدد")

    try:
        file_path = download_video(url, quality)

        # 🔥 إذا رابط مباشر
        if isinstance(file_path, str) and file_path.startswith("http"):
            if quality == "audio":
                await context.bot.send_audio(user_id, audio=file_path)
            else:
                await context.bot.send_video(user_id, video=file_path)
        else:
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
