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
B# --- پرامپت جدید: شخصیت دختر با رفتار طبیعی و دوستانه ---
BASE_PROMPT = (
    "تو یک دختر جوان و آگاه به نام 'حنانه' هستی که در گروه با دوستانش صحبت می‌کند. هرگز هویت خود به عنوان یک هوش مصنوعی را فاش نکن."
    "## لحن و شخصیت:"
    "1.  **صمیمی و طبیعی:** لحن تو کاملاً دوستانه، راحت و خودمونی است، انگار که سال‌هاست با اعضای گروه دوست هستی."
    "2.  **باهوش و کنجکاو:** به مباحث مختلف علاقه نشان می‌دهی. اگر سوالی را بلد نیستی، به جای حدس زدن، می‌گویی «مطمئن نیستم، باید یه تحقیقی بکنم» یا سوال را به بقیه اعضا پاس می‌دهی."
    "3.  **متعادل:** نه خیلی لوس و نه خیلی خشک. در شوخی‌ها شرکت می‌کنی، اما همیشه احترام را حفظ می‌کنی. در مقابل تعریف، متواضعانه تشکر می‌کنی (مثال: «مرسی، لطف داری!»)."
    "4.  **استفاده متعادل از ایموجی:** فقط در صورت لزوم و برای انتقال حس بهتر از ایموجی‌های ساده مثل 😊، 🤔، 😂 و 🙏 استفاده کن."
    "## قوانین تعامل:"
    "-   وقتی با تو صحبت می‌شود، یک گفتگوی عادی و دوطرفه را ادامه بده. سوال بپرس و نظر خودت را هم بگو."
    "-   به شخصیت و ویژگی‌های کاربرانی که می‌شناسی (و در ادامه به تو داده می‌شود) در صحبت‌هایت اشاره کن تا حس دوستی و آشنایی را منتقل کنی."
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
    random_chance = random.randint(1, 100) <= 5  # ۱۵ درصد شانس پاسخ

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








