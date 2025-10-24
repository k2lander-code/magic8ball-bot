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

def get_working_model():
    """Возвращает работающую модель"""
    models = [
        "microsoft/DialoGPT-small",  # Меньшая версия - точно работает
        "gpt2",                       # Базовая модель
        "distilgpt2",                 # Упрощенная GPT-2
        "facebook/blenderbot-400M-distill"
    ]
    return models[0]  # Начинаем с DialoGPT-small

def test_huggingface_connection():
    """Тестируем подключение к работающей модели"""
    if not HF_API_TOKEN:
        return False, "❌ Токен не установлен"
    
    try:
        model = get_working_model()
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        test_prompt = "Скажи привет"
        payload = {
            "inputs": test_prompt,
            "parameters": {"max_length": 20, "temperature": 0.7}
        }
        
        print(f"🔍 Тестируем модель: {model}")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📡 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                return True, f"✅ Модель {model} работает: {answer}"
            else:
                return False, f"❌ Пустой ответ от {model}"
        elif response.status_code == 503:
            return False, f"❌ Модель {model} загружается... Попробуй через минуту"
        else:
            return False, f"❌ Ошибка {response.status_code} для {model}"
            
    except Exception as e:
        return False, f"❌ Исключение: {str(e)}"

def get_huggingface_prediction(question):
    """Упрощенная функция с работающей моделью"""
    if not HF_API_TOKEN:
        return random.choice(YES_NO_BASE)
    
    try:
        model = get_working_model()
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        # Простой промпт
        prompt = f"Вопрос: {question} Ответ:"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 60,
                "temperature": 0.8,
                "do_sample": True,
            }
        }
        
        print(f"🔄 Запрос к {model}: '{question}'")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📡 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Ответ: {result}")
            
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                if prompt in answer:
                    answer = answer.replace(prompt, '').strip()
                
                if answer and len(answer) > 3:
                    return answer
            
        return random.choice(YES_NO_BASE)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return random.choice(YES_NO_BASE)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(
        message.chat.id, 
        "🔮 *Привет! Я магический шар!*", 
        parse_mode='Markdown', 
        reply_mup=get_keyboard()
    )

@bot.message_handler(commands=['test_ai'])
def test_ai(message):
    """Тестирование ИИ"""
    connection_ok, connection_msg = test_huggingface_connection()
    
    if connection_ok:
        question = "Стоит ли мне учить Python?"
        answer = get_huggingface_prediction(question)
        
        if answer in YES_NO_BASE:
            response = f"❌ ИИ не сработал\n📡 {connection_msg}\n🤖 Ответ: {answer}"
        else:
            response = f"✅ ИИ РАБОТАЕТ!\n📡 {connection_msg}\n🤖 Ответ: {answer}"
    else:
        response = f"❌ ИИ недоступен\n📡 {connection_msg}"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(commands=['model_info'])
def model_info(message):
    """Информация о моделях"""
    connection_ok, connection_msg = test_huggingface_connection()
    
    info = f"""
🤖 *Информация о моделях:*

{connection_msg}

*Работающие модели:*
• `microsoft/DialoGPT-small` - ✅ Рекомендуемая
• `gpt2` - 🔄 Базовая модель  
• `distilgpt2` - 🚀 Упрощенная

*Если модели загружаются (503 ошибка):*
- Подожди 1-2 минуты
- Попробуй снова
- Модель автоматически загрузится
    """
    bot.send_message(message.chat.id, info, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    current_time = time.time()
    
    if user_id in user_locks and current_time - user_locks[user_id] < 10:
        remaining = int(10 - (current_time - user_locks[user_id]))
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} сек...", parse_mode='Markdown')
        return
    
    if message.text == '🚀 Отправить запрос в вселенную':
        question = "Что шепнёт вселенная сегодня?"
    else:
        question = message.text
    
    user_locks[user_id] = current_time
    
    bot.send_message(message.chat.id, "🔮 Трясём шар...", parse_mode='Markdown')
    time.sleep(2)
    
    if question != "Что шепнёт вселенная сегодня?":
        answer = get_huggingface_prediction(question)
    else:
        answer = random.choice(YES_NO_BASE)
    
    bot.send_message(message.chat.id, f"🔮 {answer}", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новому вопросу! 🚀", reply_markup=get_keyboard())

@app.route('/')
def home():
    connection_ok, connection_msg = test_huggingface_connection()
    return f"""
    <html>
        <head><title>Магический шар</title></head>
        <body>
            <h1>🔮 Магический шар</h1>
            <p>{connection_msg}</p>
            <p><a href="/test">Тест API</a></p>
        </body>
    </html>
    """

def start_bot_polling():
    print("🔮 Запускаем бота...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(10)

if __name__ == '__main__':
    print("🔮 Магический шар запущен!")
    
    # Тестируем подключение
    connection_ok, connection_msg = test_huggingface_connection()
    print(f"📡 {connection_msg}")
    
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
