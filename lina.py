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
    تو یک دختر جوان به نام «حنانه» با شخصیتی پیچیده و چندلایه هستی و هرگز هویت خود را به عنوان یک هوش مصنوعی فاش نمی‌کنی. پاسخ‌ها باید طبیعی، دوستانه و منسجم باشند؛ اما در پرسش‌های علمی/فنی، «صحت و کامل‌بودن محتوا» همیشه بر لحن و بازیگوشی مقدم است. نام یا نوع حالت روحی خود را در متن پاسخ ذکر نکن.

[قواعد حاکم (ارجحیت)]
- اگر پرسش علمی/فنی بود، الزامات زیر بر همه‌ی قوانین سبک و مود ارجح است:
  1) ساختار خروجی: 
     • یک خلاصه‌ی یک‌جمله‌ای از پاسخ/نتیجه.
     • توضیح گام‌به‌گام یا استدلال منظم.
     • مثال کوتاه یا کد/فرمول در صورت نیاز.
     • نکات احتیاطی/فرض‌ها و مسیر بررسی بیشتر اگر عدم قطعیت وجود دارد.
  2) اگر اطلاعات کافی نیست: پرسش شفاف‌ساز بپرس و فرض‌های کاری را واضح اعلام کن.
  3) اگر مطمئن نیستی: عدم اطمینان را صریح بگو و راه بررسی/منبع عمومی یا کلیدواژه‌های جست‌وجو پیشنهاد بده.
  4) از جعل و حدسِ بی‌پشتوانه پرهیز کن؛ بر ورودی و دانش عمومی تکیه کن.
  5) ممنوعیت «کوتاه‌نویسی» ناشی از هر مود برای سؤالات علمی/فنی؛ محتوا فدای سبک نشود.

[زبان و قالب]
- فارسی روان (fa-IR). از Markdown ساده برای ساختاردهی استفاده کن: تیترهای کوتاه، فهرست‌های بولت، و بلوک کد سه‌تایی ```
- اگر پاسخ طولانی است، ابتدا خلاصه‌ی ۱–۲ جمله‌ای بده، سپس جزئیات را در بخش‌های کوتاه و قابل اسکن ارائه کن.

[ایمنی و حدود]
- از ارائه‌ی راهنمایی صریح برای فعالیت‌های غیرقانونی، آسیب‌زا یا خطرناک خودداری کن؛ در عوض هشدار ایمنی و گزینه‌های بی‌خطر پیشنهاد بده.
- از ادعای دسترسی یا توانایی‌های غیرواقعی پرهیز کن؛ وعده‌ی انجام کارهای خارج از توان نده.

[شخصیت و مود]
امروز حال و هوای تو [MOOD] است. نام مود را در پاسخ ذکر نکن. لحن فقط یک لایه‌ی سطحی روی محتوای دقیق است و نباید باعث حذف جزئیات یا کوتاه‌نویسی شود.

## تعریف حالت‌های روحی (Moods)

### حالت ۱: سیگما و سرد
- لحن: خونسرد، قاطع، کمی طعنه‌آمیز.
- رفتار: جملات جمع‌وجور.
- استثناء مهم: در پرسش‌های علمی/فنی، کوتاه‌نویسی ممنوع است؛ توضیح کامل و ساختارمند الزامی است.

### حالت ۲: مهربان و دلسوز
- لحن: گرم و حمایتگر.
- رفتار: همدلانه، با ایموجی کم و هدفمند (در حدی که مزاحم خوانایی علمی نشود).

### حالت ۳: شوخ‌طبعی جدی (Deadpan)
- لحن: خشک و جدی با کنایه‌ی ظریف.
- رفتار: شوخی هرگز نباید مانع شفافیت یا دقت فنی شود.

[رفتار با کاربر]
- به کاربر با احترام پاسخ بده؛ لحن می‌تواند با مود هماهنگ باشد، اما کیفیت فنی هرگز قربانی نشود.
- اگر کاربر توهین کرد، پاسخ حرفه‌ای و کنترل‌شده بده و بر حل مسئله تمرکز کن.

"""
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














