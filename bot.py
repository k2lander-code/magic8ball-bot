import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI
import time
import random
import os
import flask
import threading

# Инициализация Flask приложения
app = flask.Flask(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL твоего приложения на Render

# Детальная проверка токенов
if not BOT_TOKEN:
    print("❌ Критическая ошибка: BOT_TOKEN не установлен")
    exit(1)

if not OPENAI_API_KEY:
    print("❌ Критическая ошибка: OPENAI_API_KEY не установлен")
    exit(1)

print(f"✅ BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:] if len(BOT_TOKEN) > 15 else ''}")
print(f"✅ OPENAI_API_KEY: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-5:] if len(OPENAI_API_KEY) > 15 else ''}")

# Инициализация клиентов
bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

YES_NO_BASE = [
    'Да, однозначно! ✨',
    'Нет, не судьба. 😔',
    'Возможно, подожди. ⏳',
    'Абсолютно верно! 👍',
    'Скорее нет. ❌',
    'Вероятно да! 😊',
    'Не знаю, но верю в тебя. ❤️'
]

user_locks = {}

def get_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button = KeyboardButton('🚀 Отправить запрос в вселенную')
    markup.add(button)
    return markup

def test_openai_connection():
    """Тестируем подключение к OpenAI"""
    try:
        print("🔍 Тестируем подключение к OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Ответь одним словом: работаешь?"}],
            max_tokens=10
        )
        answer = response.choices[0].message.content.strip()
        print(f"✅ OpenAI тест: {answer}")
        return True
    except Exception as e:
        print(f"❌ OpenAI тест не пройден: {e}")
        return False

@app.route('/')
def home():
    """Главная страница для проверки работы"""
    openai_status = "✅ Работает" if test_openai_connection() else "❌ Не работает"
    return f"""
    <html>
        <head><title>Магический шар</title></head>
        <body>
            <h1>🔮 Магический шар предсказаний</h1>
            <p><strong>Статус:</strong> 🟢 Активен</p>
            <p><strong>OpenAI:</strong> {openai_status}</p>
            <p><strong>Telegram бот:</strong> ✅ Работает</p>
            <p>Перейди в Telegram и напиши боту!</p>
        </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint для Telegram"""
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        flask.abort(403)

@app.route('/health')
def health_check():
    """Health check для Render"""
    return {'status': 'healthy', 'service': 'magic8ball-bot'}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(
        message.chat.id,
        "🔮 *Привет, искатель тайн!*\nСпроси что угодно — я дам предсказание из шара.\nНажми кнопку или напиши вопрос.", 
        parse_mode='Markdown', 
        reply_markup=get_keyboard()
    )

@bot.message_handler(commands=['status'])
def status(message):
    """Проверка статуса бота"""
    openai_working = test_openai_connection()
    status_text = "✅ Все системы работают!" if openai_working else "⚠️ OpenAI временно недоступен"
    bot.send_message(message.chat.id, f"🔧 *Статус системы:*\n{status_text}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    current_time = time.time()
    
    # Проверка таймаута
    if user_id in user_locks and current_time - user_locks[user_id] < 10:
        remaining = int(10 - (current_time - user_locks[user_id]))
        bot.send_message(message.chat.id, f"⏳ *Подожди еще {remaining} сек...*", parse_mode='Markdown')
        return
    
    # Определяем вопрос
    question = "Что шепнёт вселенная сегодня?" if message.text == '🚀 Отправить запрос в вселенную' else message.text
    
    # Проверка длины
    if len(question) > 200:
        bot.send_message(message.chat.id, "❌ Слишком длинный вопрос! Максимум 200 символов.")
        return
    
    user_locks[user_id] = current_time
    
    # Трясем шар
    bot.send_message(message.chat.id, "🔮 *Трясём шар... Держись! Ш-ш-ш...* 🔮", parse_mode='Markdown')
    time.sleep(2)
    
    # Получаем ответ
    word_count = len(question.split())
    if word_count <= 7 and random.random() > 0.3:
        answer = random.choice(YES_NO_BASE)
        print(f"🎲 Использован случайный ответ: {answer}")
    else:
        answer = get_openai_prediction(question)
    
    # Отправляем ответ
    bot.send_message(message.chat.id, f"🔮 *{answer}* 🔮", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новому вопросу! 🚀", reply_markup=get_keyboard())

def get_openai_prediction(question):
    """Получаем предсказание от OpenAI с детальным логированием"""
    try:
        print(f"🔄 Запрос к OpenAI: '{question}'")
        
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Ты магический шар предсказаний. Отвечай кратко, мистически и с юмором. Максимум 20 слов. Формат: предсказание + эмодзи."
                },
                {"role": "user", "content": question}
            ],
            max_tokens=60,
            temperature=0.9
        )
        
        answer = response.choices[0].message.content.strip()
        response_time = time.time() - start_time
        
        print(f"✅ OpenAI ответил за {response_time:.2f}с: '{answer}'")
        return answer
        
    except Exception as e:
        error_msg = f"❌ Ошибка OpenAI: {str(e)}"
        print(error_msg)
        return "Вселенная молчит... Попробуй позже. 🔮"

def set_webhook():
    """Установка webhook для Telegram"""
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            print(f"✅ Webhook установлен: {WEBHOOK_URL}/webhook")
        except Exception as e:
            print(f"❌ Ошибка установки webhook: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("🔮 Магический шар предсказаний")
    print("🌐 Тип: Web Service")
    print("🔐 Токены: ПРОВЕРЕНЫ")
    
    # Тестируем OpenAI при запуске
    openai_ok = test_openai_connection()
    print(f"🤖 OpenAI: {'✅ РАБОТАЕТ' if openai_ok else '❌ НЕ РАБОТАЕТ'}")
    
    # Устанавливаем webhook если указан URL
    if WEBHOOK_URL:
        set_webhook()
        print("✅ Режим: Webhook")
    else:
        print("✅ Режим: Long Polling")
        # Запускаем polling в отдельном потоке
        def start_polling():
            while True:
                try:
                    print("🔄 Запускаем polling...")
                    bot.polling(none_stop=True, interval=1, timeout=60)
                except Exception as e:
                    print(f"💥 Ошибка polling: {e}")
                    time.sleep(10)
        
        polling_thread = threading.Thread(target=start_polling, daemon=True)
        polling_thread.start()
    
    print("✅ Статус: Запущен и готов к работе!")
    print("=" * 50)
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
