
import telebot
import threading
import re
from googlesearch import search
from duckduckgo_search import DDGS
import urllib.parse

# ✅ التوكن حق البوت
TOKEN = "7851307397:AAEOmk5ytN2btB9ghm488sgYNR7UYa4CWvw"
bot = telebot.TeleBot(TOKEN)

# ✅ ليستة المواقع اللي ما تلزمنيش
BLOCKED_SITES = ["una-oic.org", "youtube.com", "youtu.be", "instagram.com", "instagr.am"]

# ✅ عدد النتائج اللي تطلع
MAX_RESULTS = 20

# ✅ تخزين بيانات اليوزرز (عشان أعرف لغتهم)
user_languages = {}

# ✅ قائمة الأوامر اللي تظهر لما أكتب "/"
bot.set_my_commands([
    telebot.types.BotCommand("start", "🏁 ابدأ المحادثة"),
    telebot.types.BotCommand("language", "🌍 اختر اللغة")
])

# ✅ لما اليوزر يرسل /start
@bot.message_handler(commands=['start'])
def start_bot(message):
    chat_id = message.chat.id

    if chat_id in user_languages:
        send_welcome(message)
        return

    ask_language(message)

# ✅ أمر تغيير اللغة
@bot.message_handler(commands=['language'])
def ask_language(message):
    chat_id = message.chat.id

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("🇸🇦 عربي", "🇬🇧 English")

    bot.send_message(
        chat_id,
        "🌍 *اختر لغتك | Choose your language:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ✅ لما اليوزر يختار اللغة
@bot.message_handler(func=lambda message: message.text in ["🇸🇦 عربي", "🇬🇧 English"])
def set_language(message):
    chat_id = message.chat.id

    if message.text == "🇸🇦 عربي":
        user_languages[chat_id] = "ar"
    else:
        user_languages[chat_id] = "en"

    bot.send_message(chat_id, "✅ تم ضبط اللغة!" if user_languages[chat_id] == "ar" else "✅ Language set successfully!", reply_markup=telebot.types.ReplyKeyboardRemove())
    send_welcome(message)

# ✅ رسالة الترحيب بعد اختيار اللغة
def send_welcome(message):
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, "ar")

    welcome_text = (
        "✨💡 *مرحبًا بك في بوت العبقري سحسح!* \n\n"
        "✍️ أرسل لي *عنوان الخبر* وبدورلك على الروابط المطابقة.\n"
        "🔎 بدّور في *Google* و *DuckDuckGo* وأرسل لك الروابط المناسبة إذا لقيت عاد.\n\n"
        "📄 **إذا تبغى، برسلك النتائج في ملف PDF**\n"
        "(  والله ما قد جربتها، ولا أدري كيف تترسل بس اسوي نفسي قوي قدامك ههه 💀)."
    ) if lang == "ar" else (
        "✨💡 *Welcome to Sahar's Bot!* \n\n"
        "✍️ Send me *the news title*, and I’ll search for matching links.\n"
        "🔎 I’ll search in *Google* and *DuckDuckGo* and send you the best matches.\n\n"
        "📄 **If you want, I can send the results in a PDF file**\n"
        "(But honestly, I haven’t tried it before, hehehe 😂💀)."
    )
    
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")

# ✅ استقبال العنوان من المستخدم
@bot.message_handler(func=lambda message: message.chat.id in user_languages)
def receive_news_title(message):
    chat_id = message.chat.id
    title = message.text.strip()

    print(f"📌 العنوان المستلم: {title}")

    lang = user_languages.get(chat_id, "ar")
    bot.send_message(chat_id, "🔍 جاري البحث..." if lang == "ar" else "🔍 Searching...")

    thread = threading.Thread(target=process_news_search, args=(chat_id, title))
    thread.start()

def search_exact_news(title, lang="any"):
    results = set()
    search_query = f'{title} actualité' if lang == "fr" else f'{title} news'
    print(f"🔍 البحث عن: {search_query} | لغة البحث: {lang}")

    try:
        with DDGS() as ddgs:
            duck_results = [result['href'] for result in ddgs.text(search_query, max_results=MAX_RESULTS * 3)]

            print(f"🔵 عدد نتائج قبل الفلترة: {len(duck_results)}")
            for idx, link in enumerate(duck_results, 1):
                print(f"{idx}. {link}")  # ✅ طباعة كل رابط قبل الفلترة

            filtered_duck = [url for url in duck_results if not any(blocked in url for blocked in BLOCKED_SITES)]
            results.update(filtered_duck)
            print(f"🦆 عدد نتائج بعد الفلترة: {len(filtered_duck)}")
    except Exception as e:
        print(f"⚠️ خطأ في DuckDuckGo: {str(e)}")

    print(f"✅ عدد النتائج النهائية: {len(results)}")
    return list(results)[:MAX_RESULTS]

# ✅ تشغيل البحث وإرسال النتائج
def process_news_search(chat_id, title):
    lang = user_languages.get(chat_id, "ar")
    search_lang = "any"  # البحث بأي لغة بدون قيود

    try:
        results = search_exact_news(title, search_lang)

        if results:
            response_text = "📢 <b>تم العثور على هذه الروابط:</b> \n\n" if lang == "ar" else "📢 <b>Here are the matching links:</b> \n\n"
            for idx, link in enumerate(results, 1):
                response_text += f"{idx}. <a href='{link}'>اضغط هنا</a>\n" if lang == "ar" else f"{idx}. <a href='{link}'>Click here</a>\n"
            bot.send_message(chat_id, response_text, parse_mode="HTML", disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, "❌ لا توجد نتائج متطابقة، جرّب إعادة البحث بصياغة مختلفة." if lang == "ar" else "❌ No exact matches found, try rephrasing your query.", parse_mode="HTML")

    except Exception as e:
        bot.send_message(chat_id, f"⚠️ حدث خطأ: {str(e)}", parse_mode="HTML")

# ✅ تشغيل البوت
bot.polling(none_stop=True)
