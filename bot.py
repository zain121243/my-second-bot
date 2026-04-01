import yt_dlp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest

TOKEN = "8642196903:AAFQyss8e2IauNuHybQqy1YXg69ninwTEDE"
CHANNEL_USERNAME = "@jbt_313"

user_links = {}
processing_users = set()

# رد آمن
async def safe_reply(update, context, text, reply_markup=None):
    if update.effective_chat.type == "channel":
        return  # ❌ لا يرد داخل القناة
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup
        )

# تحقق الاشتراك (تجاهل القناة)
async def check_sub(update, context):
    if update.effective_chat.type == "channel":
        return True

    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# زر الاشتراك
def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 اشترك بالقناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("✅ تحقق", callback_data="check")]
    ])

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_sub(update, context):
        await safe_reply(update, context, "❌ اشترك أولاً", join_button())
        return
    await safe_reply(update, context, "📥 ارسل رابط الفيديو")

# استقبال الرابط
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "channel":
        return

    if not await check_sub(update, context):
        await safe_reply(update, context, "❌ اشترك أولاً", join_button())
        return

    url = update.message.text.strip()
    user_links[update.effective_user.id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎥 240p", callback_data="v240"),
            InlineKeyboardButton("🎥 360p", callback_data="v360"),
            InlineKeyboardButton("🎥 720p", callback_data="v720"),
        ],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")]
    ]

    await safe_reply(update, context, "🎯 اختر الجودة:", InlineKeyboardMarkup(keyboard))

# حل مشكلة Query القديمة
async def safe_answer(query):
    try:
        await query.answer()
    except BadRequest:
        pass

# الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    user_id = query.from_user.id

    if user_id in processing_users:
        await query.message.reply_text("⏳ انتظر...")
        return

    processing_users.add(user_id)

    try:
        if query.data == "check":
            if await check_sub(update, context):
                await query.message.reply_text("✅ تم الاشتراك")
            else:
                await query.message.reply_text("❌ بعدك")
            return

        if not await check_sub(update, context):
            await query.message.reply_text("❌ اشترك أولاً", reply_markup=join_button())
            return

        url = user_links.get(user_id)
        if not url:
            await query.message.reply_text("❌ ارسل الرابط")
            return

        await query.message.reply_text("⏳ جاري التحميل...")

        common_opts = {
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            'js_runtimes': {
                'node': {
                    'path': r"C:\Program Files\nodejs\node.exe"
                }
            }
        }

        # 🎥 فيديو
        if query.data.startswith("v"):
            quality = query.data.replace("v", "")

            ydl_opts = {
                **common_opts,
                'format': f'bestvideo[height<={quality}]+bestaudio/best'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if not filename.endswith(".mp4"):
                new_name = filename.rsplit(".", 1)[0] + ".mp4"
                os.rename(filename, new_name)
                filename = new_name

            size = os.path.getsize(filename)

            with open(filename, 'rb') as f:
                if size < 50 * 1024 * 1024:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=f,
                        read_timeout=120,
                        write_timeout=120
                    )
                else:
                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=f
                    )

            os.remove(filename)

        # 🎧 صوت
        elif query.data == "audio":
            ydl_opts = {
                **common_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            base = os.path.splitext(filename)[0]
            mp3_file = base + ".mp3"

            if not os.path.exists(mp3_file):
                mp3_file = filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")

            with open(mp3_file, 'rb') as f:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=f,
                    read_timeout=120,
                    write_timeout=120
                )

            if os.path.exists(mp3_file):
                os.remove(mp3_file)
            if os.path.exists(filename):
                os.remove(filename)

    except Exception as e:
        print(e)
        await query.message.reply_text("❌ فشل التحميل")

    finally:
        processing_users.discard(user_id)

# تشغيل
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
