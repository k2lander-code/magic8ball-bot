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

def get_huggingface_prediction(question):
    """Улучшенная функция для Hugging Face"""
    if not HF_API_TOKEN:
        print("❌ HF_API_TOKEN не установлен")
        return random.choice(YES_NO_BASE)
    
    try:
        # Пробуем разные модели
        models = [
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-large", 
            "gpt2",
            "facebook/blenderbot-400M-distill"
        ]
        
        API_URL = f"https://api-inference.huggingface.co/models/{models[0]}"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        # Улучшенный промпт
        prompt = f"""Ты - магический шар предсказаний. Ответь кратко и мистически на вопрос.
Вопрос: {question}
Ответ:"""
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 80,
                "temperature": 0.9,
                "do_sample": True,
                "return_full_text": False,
                "repetition_penalty": 1.2
            },
            "options": {
                "wait_for_model": True,
                "use_cache": True
            }
        }
        
        print(f"🔄 Запрос к Hugging Face: '{question}'")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=45)
        
        print(f"📡 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Raw ответ Hugging Face: {result}")
            
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                # Чистим ответ
                if prompt in answer:
                    answer = answer.replace(prompt, '').strip()
                if answer and len(answer) > 5:  # Проверяем что ответ не пустой
                    print(f"🎯 Очищенный ответ: '{answer}'")
                    return answer
            
            print("❌ Пустой ответ от ИИ")
            return random.choice(YES_NO_BASE)
            
        else:
            error_msg = f"❌ Ошибка API: {response.status_code} - {response.text}"
            print(error_msg)
            return random.choice(YES_NO_BASE)
            
    except Exception as e:
        error_msg = f"❌ Исключение Hugging Face: {str(e)}"
        print(error_msg)
        return random.choice(YES_NO_BASE)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(
        message.chat.id, 
        "🔮 *Привет! Я магический шар предсказаний!*\n\nЗадай мне любой вопрос, и я открою тайны вселенной!\n\nИспользуй кнопку ниже или просто напиши вопрос.", 
        parse_mode='Markdown', 
        reply_markup=get_keyboard()
    )

@bot.message_handler(commands=['test_ai'])
def test_ai(message):
    """Тестирование работы ИИ"""
    test_questions = [
        "Я найду любовь в этом году?",
        "Стоит ли мне менять работу?", 
        "Что вселенная приготовила для меня?",
        "Какой секрет ты можешь открыть?",
        "В чем мое предназначение?"
    ]
    
    question = random.choice(test_questions)
    bot.send_message(message.chat.id, f"🔍 *Тестируем ИИ...*\nВопрос: _{question}_", parse_mode='Markdown')
    
    time.sleep(2)
    
    answer = get_huggingface_prediction(question)
    bot.send_message(message.chat.id, f"🤖 *Ответ ИИ:* {answer}", parse_mode='Markdown')
    
    print(f"🧪 Тест ИИ: '{question}' → '{answer}'")

@bot.message_handler(commands=['debug'])
def debug_info(message):
    """Информация для отладки"""
    info = f"""
🔧 *Информация для отладки:*
• 🤖 Hugging Face: {'✅ Настроен' if HF_API_TOKEN else '❌ Не настроен'}
• 🔮 Режим: Web Service
• 📍 Статус: Активен

*Тестовые вопросы для ИИ:*
1. "Я найду любовь?"
2. "Что ждет меня завтра?"
3. "Стоит ли рискнуть?"
4. "Какой секрет вселенной?"
5. "В чем мое предназначение?"
    """
    bot.send_message(message.chat.id, info, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_check(message):
    """Проверка статуса бота"""
    status_msg = f"""
🔮 *Статус магического шара:*
• 🤖 AI: {'✅ Активен' if HF_API_TOKEN else '❌ Только базовые ответы'}
• ⚡ Сервер: 🟢 Работает
• 🎯 Готов к вопросам: ✅ Да

*Попробуй спросить:*
"Что ждет меня сегодня?"
"Стоит ли доверять интуиции?"
"Какой совет даст вселенная?"
    """
    bot.send_message(message.chat.id, status_msg, parse_mode='Markdown')

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
    
    # Трясем шар
    bot.send_message(message.chat.id, "🔮 *Трясём шар... Держись! Ш-ш-ш...* 🔮", parse_mode='Markdown')
    time.sleep(2)
    
    # Получаем ответ
    word_count = len(question.split())
    if word_count <= 7 and random.random() > 0.3:
        answer = random.choice(YES_NO_BASE)
        print(f"🎲 Использован случайный ответ: {answer}")
    else:
        answer = get_huggingface_prediction(question)
        print(f"🤖 AI ответ: {answer}")
    
    # Отправляем ответ
    bot.send_message(message.chat.id, f"🔮 *{answer}* 🔮", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новому вопросу! 🚀", reply_markup=get_keyboard())

# Flask маршруты для Web Service
@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Магический шар предсказаний</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container { 
                    background: rgba(255,255,255,0.1); 
                    padding: 30px; 
                    border-radius: 15px; 
                    backdrop-filter: blur(10px);
                }
                h1 { text-align: center; }
                .status { 
                    background: rgba(255,255,255,0.2); 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin: 10px 0; 
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔮 Магический шар предсказаний</h1>
                <div class="status">
                    <p><strong>Статус:</strong> 🟢 Активен</p>
                    <p><strong>Telegram бот:</strong> ✅ Работает</p>
                    <p><strong>AI Модель:</strong> 🤖 Hugging Face</p>
                    <p><strong>Режим:</strong> Web Service + Long Polling</p>
                </div>
                <p>Бот работает в фоновом режиме и готов отвечать на ваши вопросы в Telegram!</p>
                <p>Перейдите в Telegram и напишите боту чтобы получить предсказание.</p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'magic8ball-bot', 'timestamp': time.time()}

@app.route('/test')
def test_huggingface():
    """Тестовый endpoint для проверки Hugging Face"""
    try:
        test_question = "Что ждет человечество в будущем?"
        answer = get_huggingface_prediction(test_question)
        return {
            'question': test_question,
            'answer': answer,
            'ai_working': 'hugging_face' not in answer.lower() and answer not in YES_NO_BASE
        }
    except Exception as e:
        return {'error': str(e)}

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
    print("🔮 Магический шар предсказаний")
    print("🌐 Тип: Web Service")
    print("🤖 Hugging Face: ✅ Доступен" if HF_API_TOKEN else "🤖 Hugging Face: ❌ Не настроен")
    print("🎯 Статус: Запущен и готов к работе!")
    print("=" * 60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    print(f"🌍 Web сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
