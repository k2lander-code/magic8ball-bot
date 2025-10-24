import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import random
import os
import requests
import threading
from flask import Flask

# Инициализация Flask для Web Service
app = Flask(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

# Проверка токенов
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не установлен")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

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

def get_huggingface_prediction(question):
    if not HF_API_TOKEN:
        return random.choice(YES_NO_BASE)
    
    try:
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        prompt = f"Ты - магический шар предсказаний. Ответь кратко и мистически: {question}"
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 60, "temperature": 0.9}
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            answer = result[0]['generated_text'].strip()
            return answer if answer else random.choice(YES_NO_BASE)
        return random.choice(YES_NO_BASE)
            
    except Exception as e:
        print(f"❌ Ошибка Hugging Face: {e}")
        return random.choice(YES_NO_BASE)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(
        message.chat.id, 
        "🔮 *Привет! Я магический шар!*\nСпроси что угодно — я дам предсказание!", 
        parse_mode='Markdown', 
        reply_markup=get_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    current_time = time.time()
    
    if user_id in user_locks and current_time - user_locks[user_id] < 10:
        remaining = int(10 - (current_time - user_locks[user_id]))
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} сек...", parse_mode='Markdown')
        return
    
    question = "Что шепнёт вселенная?" if message.text == '🚀 Отправить запрос в вселенную' else message.text
    user_locks[user_id] = current_time
    
    bot.send_message(message.chat.id, "🔮 Трясём шар... Ш-ш-ш...", parse_mode='Markdown')
    time.sleep(2)
    
    word_count = len(question.split())
    if word_count <= 7 and random.random() > 0.3:
        answer = random.choice(YES_NO_BASE)
    else:
        answer = get_huggingface_prediction(question)
    
    bot.send_message(message.chat.id, f"🔮 *{answer}*", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новому вопросу! 🚀", reply_markup=get_keyboard())

# Flask маршруты для Web Service
@app.route('/')
def home():
    return """
    <html>
        <head><title>Магический шар</title></head>
        <body>
            <h1>🔮 Магический шар предсказаний</h1>
            <p><strong>Статус:</strong> 🟢 Активен</p>
            <p><strong>Telegram бот:</strong> ✅ Работает</p>
            <p>Бот работает в фоновом режиме через long-polling</p>
        </body>
    </html>
    """

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'magic8ball-bot'}

def start_bot_polling():
    """Запуск бота в отдельном потоке"""
    print("🔮 Запускаем Telegram бота...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(f"❌ Ошибка бота: {e}")
            time.sleep(10)

if __name__ == '__main__':
    print("🔮 Магический шар запущен как Web Service!")
    print(f"🤖 Hugging Face: {'✅ Доступен' if HF_API_TOKEN else '❌ Не настроен'}")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
