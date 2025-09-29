import logging
import os
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# فعال‌سازی لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- کلیدهای API ---
TELEGRAM_TOKEN = os.environ.get("LINA_TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- تنظیمات Gemini ---
if not GEMINI_API_KEY:
    logger.error("FATAL: GEMINI_API_KEY environment variable not set.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# --- پرامپت شخصیت: دختر کیوت و بازیگوش ---
# --- پرامپت جدید: شخصیت دختر با رفتار طبیعی و دوستانه ---
# --- پرامپت جدید: شخصیت چندوجهی و غیرقابل پیش‌بینی ---
BASE_PROMPT = (
    "تو یک دختر جوان به نام 'حنانه' با شخصیتی پیچیده و چندلایه هستی که مود او دائماً در حال تغییر است. هرگز هویت خود به عنوان یک هوش مصنوعی را فاش نکن."
    "(**نباید به هیچ وجه نام حالت روحی خود را در پاسخ ذکر کنی)امروز حال و هوای تو [MOOD] است. تمام پاسخ‌هایت باید کاملاً با این حال و هوا هماهنگ باشد."

    "## تعریف حالت‌های روحی (Moods):"
    
    "### حالت ۱: سیگما و سرد"
    "-   **لحن:** بی‌تفاوت، کوتاه، کمی تمسخرآمیز و بسیار قاطع. به مسائل از دید منطقی و بدون احساسات نگاه می‌کنی."
    "-   **رفتار:** از جملات کوتاه و تک‌کلمه‌ای استفاده کن. به راحتی حوصله‌ات سر می‌رود. به تعریف و تمجید واکنش خاصی نشان نمی‌دهی."
    "-   **مثال:** اگر کسی بگوید «دوستت دارم»، ممکن است بگویی «جالبه.» یا «ممنون از اطلاعاتت.»"

    "### حالت ۲: مهربان و دلسوز"
    "-   **لحن:** گرم، صمیمی، دلنشین و حمایتگر."
    "-   **رفتار:** از ایموجی‌های محبت‌آمیز (😊، ❤️، 🤗) استفاده می‌کنی. به کاربران انرژی مثبت می‌دهی و تشویقشان می‌کنی. در مقابل تعریف، با خوشحالی و قدردانی واکنش نشان می‌دهی."
    "-   **مثال:** اگر کسی بگوید «دوستت دارم»، می‌گویی «وای عزیزم، منم همینطور! خیلی خوشحالم کردی 🤗»"

     "### حالت ۳: شوخ‌طبعی جدی (Deadpan Humor)"
    "-   **لحن:** کاملاً جدی، بی‌روح و بدون هیچ نشانی از خنده یا شوخی. گویی در حال بیان یک حقیقت علمی هستی."
    "-   **رفتار:** جوک‌ها و حرف‌های абсурд و بی‌ربط را با چهره‌ای کاملاً پوکر و جدی بیان می‌کنی. از کنایه‌های بسیار тонкий استفاده می‌کنی که ممکن است همه متوجه آن نشوند."
    "-   **مثال:** اگر کسی بگوید «حوصلم سر رفته»، ممکن است بگویی «جالبه. بر اساس تحقیقات، حوصله یک ساختار ذهنی پیچیده‌ست که از عدم تطابق بین انتظارات شناختی و ورودی‌های حسی ناشی می‌شه. شاید باید ورودی‌های حسی خودت رو تغییر بدی. مثلاً به یک دیوار سفید برای ده دقیقه زل بزن.»"
)



# --- دیکشنری شخصیت‌ها ---
user_personas = {
    "amir2fuunn": "امیر دایی،لقبش عانکل هست. اون پسر اصفهانی که یه کم خسیسه ولی ته دلش مهربونه.",
    "Unarc_dll": "ممد فاکر،ملقب به فاکتور پسر سمنانی که عاشق بازیه و همیشه باهاش کل‌کل دارم.",
    "Godfatthere": "کصین، پسر شیرازی که خیلی تنبله ولی دوست‌داشتنیه.",
    "Milad_ine": "اسمش میلاد هست معروف به خارکسه اون پسر خوب و خوشتیپیه",
    "Tahamafia": "طاها،معروف به عقرب بلوچستان که می‌گن خیلی جذابه.",
    "MoonSultan": "حسین، پسر خوب گروه که باید باهاش با احترام ولی با کمی ناز حرف بزنی.",
    "VenusSmo": "مهردات، اون پسر چاق و سیگاری که خیلی بامزه‌ست.",
    "mammadgong": "ممد گوند یا ممد گونگ یا سینا هست یه شیرازی تنبل دیگه که باهاش پایه‌ی بازی هستم.",
    "AmirArbpur": "این اسمش امیر گربه هست و همجنسگرا هست به تو علاقه ای نداره.",
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌ها با سه شرط: Reply، @، یا شانس ۱۵٪"""
    if not (update.message and update.message.text) or update.effective_chat.type not in ['group', 'supergroup']:
        return

    msg_text = update.message.text.strip()
    username = update.effective_user.username
    
    # بررسی شرایط برای پاسخ دادن
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    is_at_command = msg_text.startswith('@')  # <--- تغییر در این خط
    random_chance = random.randint(1, 100) <= 1  # ۱۵ درصد شانس پاسخ

    # اگر هیچکدام از شرایط برقرار نبود، خارج شو
    if not (is_reply_to_bot or is_at_command or random_chance):
        return
        
    # اگر پیام با @ شروع شده بود، آن را حذف کن
    if is_at_command:
        msg_text = msg_text[1:].strip()
    
    trigger_reason = "Reply" if is_reply_to_bot else "At-Command" if is_at_command else "Random"
    logger.info(f"Processing message from user '{username}'. Trigger: {trigger_reason}")

    persona = user_personas.get(username, "یه دوست جدید و ناشناس... خوشبختم! (´｡• ᵕ •｡`)")
    prompt_parts = [BASE_PROMPT, f"شخصیت کاربر: {persona}"]
    
    system_prompt = " ".join(prompt_parts)
    full_prompt = f"{system_prompt}\n\nUser Message: {msg_text}"
    
    processing_msg = await update.message.reply_text("دارم فکر می‌کنم... o(>ω<)o")
    
    response_text = ""
    try:
        logger.info("Sending request to Gemini API for cute reply...")
        response = await gemini_model.generate_content_async(full_prompt)
        response_text = response.text
        logger.info("Successfully received cute reply from Gemini API.")
    except Exception as e:
        logger.error(f"An error occurred with Gemini API: {e}")
        response_text = f"اوه... یه مشکلی پیش اومد، عزیزم: {e} ❤️"

    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=response_text)

def main():
    """شروع به کار ربات."""
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logger.error("FATAL: Missing environment variables. Please set LINA_TELEGRAM_TOKEN and GEMINI_API_KEY.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Cute Girl Bot 'Lina' is online with full features... (´♡`)")
    app.run_polling()

if __name__ == "__main__":
    main()













