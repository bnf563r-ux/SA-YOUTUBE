import os
import tempfile
from pytubefix import YouTube
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط يوتيوب لتحميله 🎥")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("⏳ جاري التحميل...")
    
    try:
        # إنشاء كائن يوتيوب
        yt = YouTube(url)
        
        # اختيار أفضل فيديو فيه صوت
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            await msg.edit_text("❌ لم أجد فيديو مناسب للتحميل")
            return
        
        # مسار مؤقت
        temp_dir = tempfile.mkdtemp()
        file_path = stream.download(output_path=temp_dir)
        
        # إرسال الفيديو
        await msg.edit_text("📤 جاري الإرسال...")
        with open(file_path, "rb") as video:
            await update.message.reply_video(video, caption=yt.title)
        
        os.remove(file_path)
        os.rmdir(temp_dir)
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ:\n{e}")

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN غير موجود!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    app.run_polling()

if __name__ == "__main__":
    main()
