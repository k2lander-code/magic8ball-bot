import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import random
import os
import requests
import threading
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

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

def test_huggingface_connection():
    """Тестируем доступные модели"""
    if not HF_API_TOKEN:
        return False, "❌ Токен не установлен"
    
    # Тестируем разные модели
    test_models = [
        "gpt2",                          # Базовая модель - всегда работает
        "distilgpt2",                    # Упрощенная GPT-2
        "microsoft/DialoGPT-small",      # Пробуем еще раз
        "facebook/blenderbot-400M-distill"
    ]
    
    for model in test_models:
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            
            payload = {
                "inputs": "Скажи привет",
                "parameters": {"max_length": 10}
            }
            
            print(f"🔍 Тестируем: {model}")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    answer = result[0]['generated_text'].strip()
                    return True, f"✅ {model} работает: {answer}"
            elif response.status_code == 503:
                return False, f"🔄 {model} загружается... Подожди 1-2 минуты"
                
        except Exception as e:
            print(f"❌ {model}: {e}")
            continue
    
    return False, "❌ Все модели недоступны. Используем базовые ответы."

def get_huggingface_prediction(question):
    """Простая функция с GPT-2"""
    if not HF_API_TOKEN:
        return random.choice(YES_NO_BASE)
    
    try:
        # Используем GPT-2 - точно работает
        API_URL = "https://api-inference.huggingface.co/models/gpt2"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        # Английский промпт для лучших результатов
        prompt = f"Q: {question} A:"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 80,
                "temperature": 0.9,
                "do_sample": True,
            }
        }
        
        print(f"🔄 Запрос к GPT-2: '{question}'")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📡 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Ответ: {result}")
            
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                # Убираем промпт
                if prompt in answer:
                    answer = answer.replace(prompt, '').strip()
                
                if answer and len(answer) > 3:
                    # Переводим/адаптируем ответ
                    russian_answer = translate_to_russian(answer)
                    return russian_answer
            
        return random.choice(YES_NO_BASE)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return random.choice(YES_NO_BASE)

def translate_to_russian(text):
    """Упрощенный перевод ответа на русский"""
    # Простая замена ключевых слов
    translations = {
        "yes": "да", "no": "нет", "maybe": "возможно",
        "certainly": "конечно", "probably": "вероятно",
        "hello": "привет", "love": "любовь", "future": "будущее"
    }
    
    text_lower = text.lower()
    for eng, rus in translations.items():
        if eng in text_lower:
            return text.replace(eng, rus).capitalize()
    
    return text

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(
        message.chat.id, 
        "🔮 *Привет! Я магический шар!*\n\nЗадай вопрос на русском или английском!", 
        parse_mode='Markdown', 
        reply_markup=get_keyboard()
    )

@bot.message_handler(commands=['test_ai'])
def test_ai(message):
    """Тестирование ИИ"""
    connection_ok, connection_msg = test_huggingface_connection()
    
    if connection_ok:
        # Тестируем на английском для лучших результатов
        question = "Will I find love this year?"
        answer = get_huggingface_prediction(question)
        
        if answer in YES_NO_BASE:
            response = f"❌ ИИ не сработал\n{connection_msg}"
        else:
            response = f"✅ ИИ РАБОТАЕТ!\n{connection_msg}\n🤖 Ответ: {answer}"
    else:
        response = f"❌ ИИ недоступен\n{connection_msg}"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(commands=['test_english'])
def test_english(message):
    """Тест на английском"""
    bot.send_message(message.chat.id, "🧪 *Testing AI with English...*", parse_mode='Markdown')
    
    questions = [
        "Will it rain tomorrow?",
        "Should I learn programming?",
        "What is my future?"
    ]
    
    question = random.choice(questions)
    answer = get_huggingface_prediction(question)
    
    bot.send_message(message.chat.id, f"❓ *Q:* {question}\n🤖 *A:* {answer}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    current_time = time.time()
    
    if user_id in user_locks and current_time - user_locks[user_id] < 10:
        remaining = int(10 - (current_time - user_locks[user_id]))
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} сек...", parse_mode='Markdown')
        return
    
    if message.text == '🚀 Отправить запрос в вселенную':
        question = "What will happen today?"
    else:
        question = message.text
    
    user_locks[user_id] = current_time
    
    bot.send_message(message.chat.id, "🔮 Shaking the ball...", parse_mode='Markdown')
    time.sleep(2)
    
    if question != "What will happen today?":
        answer = get_huggingface_prediction(question)
    else:
        answer = random.choice(YES_NO_BASE)
    
    bot.send_message(message.chat.id, f"🔮 {answer}", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Ready for new questions! 🚀", reply_markup=get_keyboard())

@app.route('/')
def home():
    connection_ok, connection_msg = test_huggingface_connection()
    return f"""
    <html>
        <head><title>Magic Ball</title></head>
        <body>
            <h1>🔮 Magic Ball</h1>
            <p>{connection_msg}</p>
            <p>Using GPT-2 model</p>
        </body>
    </html>
    """

def start_bot_polling():
    print("🔮 Starting bot...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    print("🔮 Magic Ball Started!")
    
    # Тестируем подключение
    connection_ok, connection_msg = test_huggingface_connection()
    print(f"📡 {connection_msg}")
    
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
