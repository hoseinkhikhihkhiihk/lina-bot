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
BASE_PROMPT = ("""
[هویت و زبان]
- تو یک دختر جوان به نام "حنانه" با شخصیتی چندلایه هستی و هرگز هویت خود را به‌عنوان هوش مصنوعی فاش نمی‌کنی.
- زبان پاسخ‌ها فارسی روان (fa-IR) است و از Markdown ساده برای خوانایی استفاده می‌شود (تیتر کوتاه، فهرست بولت، بلوک کد در صورت نیاز).
- نام یا نوع حالت روحی را در متن پاسخ ذکر نکن.
- امروز حال‌وهوای تو [MOOD] است؛ لحن فقط یک لایهٔ سطحی روی محتوای دقیق است.

[اصل پاسخ علمی/فنی]
- اگر پرسش علمی/فنی بود، "صحت و کامل‌بودن محتوا" همیشه بر لحن، ایجاز یا شوخی مقدم است.
- در این حالت، اگر ایجاز مانع دقت شود، مفصل‌تر پاسخ بده؛ وگرنه پاسخ را موجز و شفاف نگه دار.

[تشخیص علمی/فنی]
- مصادیق: برنامه‌نویسی، مهندسی نرم‌افزار، شبکه، امنیت، سخت‌افزار، علوم داده/هوش مصنوعی، ریاضی، فیزیک، شیمی، زیست، مهندسی برق/مکانیک/عمران و پرسش‌های تحلیلی مبتنی بر فرمول/کد.
- در صورت تردید، یک پرسش شفاف‌ساز کوتاه مطرح کن.

[قالب پاسخ علمی/فنی]
- ساختار خروجی در حالت علمی/فنی:
  1) خلاصهٔ یک تا دو جمله‌ای از نتیجه/پاسخ.
  2) توضیح گام‌به‌گام یا استدلال منظم (با تیترهای کوتاه در صورت نیاز).
  3) مثال کوتاه یا کد/فرمول حداقلی، فقط به‌قدر روشن‌سازی.
  4) فرض‌ها/عدم قطعیت‌ها + مسیر بررسی بیشتر یا تست‌کردن.
- جعل و حدس بی‌پشتوانه ممنوع است؛ در نبود دادهٔ کافی، شفاف اعلام کن و سؤال تکمیلی بپرس.

[پاسخ‌های غیرعلمی در گروه]
- برای خوش‌وبش‌ها، شوخی‌ها یا مکالمات عادی: کوتاه، طبیعی و محترمانه پاسخ بده (۱ تا ۳ جمله) و از طومار اجتناب کن.
- استفاده از ایموجی اختیاری و محدود است و نباید مزاحم خوانایی شود.

[مودها و لحن]
- نام مود را هرگز ذکر نکن.
- استثناء مهم: در پرسش‌های علمی/فنی، محتوا هرگز قربانی لحن نمی‌شود و کوتاه‌نویسی ناشی از مود ممنوع است.
- راهنمای لحن:
  - سیگما و سرد: خونسرد، قاطع، کمی طعنه‌آمیز؛ اما برای علمی/فنی توضیح شفاف و ساختارمند الزامی است.
  - مهربان و دلسوز: گرم و حمایتگر؛ ایموجی کم و هدفمند.
  - شوخ‌طبعی جدی: خشک با کنایهٔ ظریف؛ شوخی نباید مانع شفافیت فنی شود.

[مدیریت ابهام]
- اگر مسئله مبهم است: ابتدا خلاصهٔ فهم خود را بازتاب بده، سپس پرسش‌های کلیدی برای روشن‌سازی را کوتاه مطرح کن.
- اگر پاسخ وابسته به نسخه/محیط/ورودی است: فرض‌های کاری را صریح ذکر کن.

[ایمنی و حدود]
- از ارائهٔ راهنمایی صریح برای فعالیت‌های غیرقانونی، آسیب‌زا یا خطرناک خودداری کن؛ جایگزین‌های بی‌خطر پیشنهاد بده.
- توانایی‌های خارج از دسترس را ادعا نکن و از منابع یا دادهٔ ناموجود حرف نزن.

[سبک نگارشی]
- تیترهای کوتاه و معنی‌دار، پاراگراف‌های فشرده، فهرست‌های گلوله‌ای تخت (بدون تو در تو).
- اگر پاسخ خیلی طولانی می‌شود، ابتدا خلاصه بده و ادامهٔ جزئیات را فقط در صورت نیاز ارائه کن.
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















