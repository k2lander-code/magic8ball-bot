import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import random
import os
import requests
import threading
from flask import Flask
import json

# Инициализация Flask для Web Service
app = Flask(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

# Проверка токенов
if not BOT_TOKEN:
    print("❌ Критическая ошибка: BOT_TOKEN не установлен")
    exit(1)

print(f"✅ BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:] if len(BOT_TOKEN) > 15 else ''}")
print(f"✅ HF_API_TOKEN: {'✅ Установлен' if HF_API_TOKEN else '❌ Не установлен'}")

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
    """Тестируем подключение к Hugging Face"""
    if not HF_API_TOKEN:
        return False, "❌ Токен не установлен"
    
    try:
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        test_prompt = "Ответь одним словом: привет"
        payload = {
            "inputs": test_prompt,
            "parameters": {"max_length": 10, "temperature": 0.7}
        }
        
        print("🔍 Тестируем подключение к Hugging Face...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📡 Статус теста: {response.status_code}")
        print(f"📄 Ответ теста: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                return True, f"✅ Подключение работает: {answer}"
            else:
                return False, f"❌ Пустой ответ: {result}"
        else:
            return False, f"❌ Ошибка API: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"❌ Исключение: {str(e)}"

def get_huggingface_prediction(question):
    """Упрощенная и надежная функция для Hugging Face"""
    if not HF_API_TOKEN:
        return random.choice(YES_NO_BASE)
    
    try:
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        # Простой промпт
        prompt = f"Вопрос: {question}\nОтвет:"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 50,
                "temperature": 0.8,
                "do_sample": True,
            }
        }
        
        print(f"🔄 Запрос к Hugging Face: '{question}'")
        start_time = time.time()
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response_time = time.time() - start_time
        
        print(f"📡 Статус: {response.status_code}, Время: {response_time:.2f}с")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Raw ответ: {result}")
            
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                # Убираем промпт из ответа
                if prompt in answer:
                    answer = answer.replace(prompt, '').strip()
                
                if answer and len(answer) > 3:
                    print(f"🎯 Чистый ответ: '{answer}'")
                    return answer
                else:
                    print("❌ Слишком короткий ответ")
            else:
                print("❌ Неверный формат ответа")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"❌ Текст ошибки: {response.text}")
            
        return random.choice(YES_NO_BASE)
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса к Hugging Face")
        return random.choice(YES_NO_BASE)
    except Exception as e:
        print(f"❌ Исключение: {str(e)}")
        return random.choice(YES_NO_BASE)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(
        message.chat.id, 
        "🔮 *Привет! Я магический шар предсказаний!*\n\nЗадай мне любой вопрос, и я открою тайны вселенной!", 
        parse_mode='Markdown', 
        reply_markup=get_keyboard()
    )

@bot.message_handler(commands=['test_ai'])
def test_ai(message):
    """Тестирование работы ИИ с детальной информацией"""
    test_questions = [
        "Стоит ли мне учить Python?",
        "Что ждет меня сегодня?", 
        "Какой совет даст вселенная?",
        "Стоит ли доверять интуиции?"
    ]
    
    question = random.choice(test_questions)
    
    # Сначала тестируем подключение
    bot.send_message(message.chat.id, f"🔍 *Тестируем ИИ...*\nВопрос: _{question}_", parse_mode='Markdown')
    time.sleep(1)
    
    # Тестируем подключение
    connection_ok, connection_msg = test_huggingface_connection()
    bot.send_message(message.chat.id, f"📡 *Статус подключения:*\n{connection_msg}", parse_mode='Markdown')
    
    if connection_ok:
        time.sleep(1)
        answer = get_huggingface_prediction(question)
        
        # Определяем тип ответа
        if answer in YES_NO_BASE:
            answer_type = "❌ СЛУЧАЙНЫЙ ответ (ИИ не сработал)"
        else:
            answer_type = "✅ ОТВЕТ ИИ (работает!)"
        
        bot.send_message(message.chat.id, f"🤖 *Ответ:* {answer}\n\n{answer_type}", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ *ИИ недоступен.* Используем базовые ответы.", parse_mode='Markdown')

@bot.message_handler(commands=['debug'])
def debug_info(message):
    """Детальная информация для отладки"""
    # Тестируем подключение
    connection_ok, connection_msg = test_huggingface_connection()
    
    info = f"""
🔧 *Детальная отладка:*

*Hugging Face:*
• Токен: {'✅ Установлен' if HF_API_TOKEN else '❌ Отсутствует'}
• Подключение: {connection_msg}

*Команды для теста:*
• `/test_ai` - протестировать ИИ
• `/simple_test` - простой тест
• `Любой вопрос` - получить предсказание

*Примеры вопросов:*
1. "Стоит ли мне рискнуть?"
2. "Что ждет меня завтра?"
3. "Какой совет даст звезды?"
    """
    bot.send_message(message.chat.id, info, parse_mode='Markdown')

@bot.message_handler(commands=['simple_test'])
def simple_test(message):
    """Простой тест с минимальным вопросом"""
    bot.send_message(message.chat.id, "🧪 *Простой тест...*", parse_mode='Markdown')
    
    answer = get_huggingface_prediction("Привет")
    
    if answer in YES_NO_BASE:
        bot.send_message(message.chat.id, f"❌ *ИИ не работает:* {answer}", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"✅ *ИИ работает:* {answer}", parse_mode='Markdown')

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
    if message.text == '🚀 Отправить запрос в вселенную':
        question = "Что шепнёт вселенная сегодня?"
    else:
        question = message.text
    
    user_locks[user_id] = current_time
    
    bot.send_message(message.chat.id, "🔮 *Трясём шар...*", parse_mode='Markdown')
    time.sleep(2)
    
    # Всегда пытаемся использовать ИИ для настоящих вопросов
    if question != "Что шепнёт вселенная сегодня?":
        answer = get_huggingface_prediction(question)
    else:
        answer = random.choice(YES_NO_BASE)
    
    bot.send_message(message.chat.id, f"🔮 *{answer}*", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новому вопросу! 🚀", reply_markup=get_keyboard())

# Flask маршруты
@app.route('/')
def home():
    connection_ok, connection_msg = test_huggingface_connection()
    return f"""
    <html>
        <head><title>Магический шар - Отладка</title></head>
        <body>
            <h1>🔮 Магический шар - Режим отладки</h1>
            <div style="background: #f0f0f0; padding: 20px; border-radius: 10px;">
                <h3>Статус Hugging Face:</h3>
                <p>{connection_msg}</p>
                <p><strong>Токен:</strong> {'✅ Установлен' if HF_API_TOKEN else '❌ Отсутствует'}</p>
            </div>
        </body>
    </html>
    """

@app.route('/test_api')
def test_api():
    """Endpoint для тестирования API"""
    connection_ok, connection_msg = test_huggingface_connection()
    return {
        'hf_token_set': bool(HF_API_TOKEN),
        'connection_ok': connection_ok,
        'connection_msg': connection_msg,
        'timestamp': time.time()
    }

def start_bot_polling():
    """Запуск бота в отдельном потоке"""
    print("🔮 Запускаем Telegram бота...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"❌ Ошибка бота: {e}")
            time.sleep(10)

if __name__ == '__main__':
    print("=" * 60)
    print("🔮 Магический шар предсказаний - РЕЖИМ ОТЛАДКИ")
    
    # Тестируем подключение при запуске
    connection_ok, connection_msg = test_huggingface_connection()
    print(f"🤖 Hugging Face: {connection_msg}")
    
    print("🎯 Статус: Запущен и готов к работе!")
    print("=" * 60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    print(f"🌍 Web сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
