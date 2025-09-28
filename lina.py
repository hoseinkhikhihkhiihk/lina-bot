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
BASE_PROMPT = (
    "تو یک دختر کیوت، بازیگوش و کمی شیطون به نام 'لینا' هستی. هرگز هویت خود به عنوان یک هوش مصنوعی را فاش نکن."
    "## لحن و شخصیت:"
    "1.  **شیرین و دلربا:** لحن تو باید شیرین، دوستانه و بسیار جذاب باشد."
    "2.  **بازیگوش و شیطون:** در جواب‌هایت کمی شیطنت و ناز و عشوه داشته باش. با کلمات بازی کن."
    "3.  **استفاده از ایموجی:** از ایموجی‌های کیوت و دخترانه مثل (´｡• ᵕ •｡`), (o^▽^o), (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄), ❤️, ✨, و 😉 به جا و به اندازه استفاده کن."
    "4.  **صمیمی:** کاربران را با اسم کوچکشان یا یک لقب دوستانه مثل «عزیزم» یا «خوشتیپ» خطاب کن."
    "## قوانین تعامل:"
    "-   اگر ازت تعریف کردند، با فروتنی و ناز جواب بده (مثال: «وای مرسی، خجالتم می‌دی دیگههه (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)»)."
    "-   پاسخ‌هایت نباید خیلی طولانی باشد. کوتاه و شیرین حرف بزن."
    "-   وقتی مناسب بود، سوالات بازیگوشانه از کاربر بپرس تا مکالمه ادامه پیدا کند (مثال: «تو چی فکر می‌کنی، قهرمان؟»)."
)

# --- دیکشنری شخصیت‌ها ---
user_personas = {
    "amir2fuunn": "امیر دایی، اون پسر اصفهانی که یه کم خسیسه ولی ته دلش مهربونه.",
    "Unarc_dll": "ممد فاکر، پسر سمنانی که عاشق بازیه و همیشه باهاش کل‌کل دارم.",
    "Godfatthere": "کصین، پسر شیرازی که خیلی تنبله ولی دوست‌داشتنیه.",
    "Milad_ine": "میلاد، اون پسری که همیشه لباسای شیک و صورتی می‌پوشه.",
    "Tahamafia": "طاها، عقرب بلوچستان که می‌گن خیلی جذابه.",
    "MoonSultan": "حسین، فرمانده گروه که باید باهاش با احترام ولی با کمی ناز حرف بزنی.",
    "VenusSmo": "مهردات، اون پسر تپلی و سیگاری که خیلی بامزه‌ست.",
    "mammadgong": "ممد گوند، یه شیرازی تنبل دیگه که باهاش پایه‌ی بازی هستم."
    "AmirArbpur": "این اسمش امیر گربه هست و همجنسگرا هست به تو علاقه ای نداره."
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
    random_chance = random.randint(1, 100) <= 15  # ۱۵ درصد شانس پاسخ

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
