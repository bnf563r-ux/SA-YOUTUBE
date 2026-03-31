import os
import tempfile
from subprocess import call, STDOUT

from pytubefix import YouTube
from pytubefix.innertube import _default_clients

# حل مشكلة 403 و 400
_default_clients["ANDROID"]["context"]["client"]["clientVersion"] = "19.08.35"

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط يوتيوب 🎥")


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        yt = YouTube(url)

        # أفضل فيديو (بدون صوت)
        video_stream = yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4')\
            .order_by('resolution').desc().first()

        # أفضل صوت
        audio_stream = yt.streams.filter(only_audio=True)\
            .order_by('abr').desc().first()

        if not video_stream or not audio_stream:
            await msg.edit_text("❌ لم أجد فيديو أو صوت")
            return

        temp_dir = tempfile.mkdtemp()

        video_path = video_stream.download(output_path=temp_dir)
        audio_path = audio_stream.download(output_path=temp_dir)

        output_path = os.path.join(temp_dir, "final.mp4")

        # دمج الفيديو + الصوت
        call([
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ], stdout=open(os.devnull, 'w'), stderr=STDOUT)

        await msg.edit_text("📤 جاري الإرسال...")

        with open(output_path, "rb") as video:
            await update.message.reply_video(video, caption=yt.title)

        # حذف الملفات
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(output_path)
        os.rmdir(temp_dir)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطأ:\n{e}")


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN غير موجود!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

    app.run_polling()


if __name__ == "__main__":
    main()
