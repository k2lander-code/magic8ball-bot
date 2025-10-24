import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import random
import os
import requests

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

def test_alternative_models():
    """Тестируем разные модели"""
    models_to_test = [
        "distilgpt2",
        "microsoft/DialoGPT-small", 
        "facebook/blenderbot-400M-distill",
        "EleutherAI/gpt-neo-125M",
        "google/flan-t5-small"
    ]
    
    results = []
    for model in models_to_test:
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            
            payload = {"inputs": "Hello", "parameters": {"max_length": 10}}
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                results.append(f"✅ {model} - РАБОТАЕТ")
            else:
                results.append(f"❌ {model} - {response.status_code}")
                
        except Exception as e:
            results.append(f"❌ {model} - Ошибка")
    
    return "\n".join(results)

def get_simple_ai_response(question):
    """Простая AI логика на базовых правилах"""
    question_lower = question.lower()
    
    # Простые правила для ответов
    if any(word in question_lower for word in ['любовь', 'love', 'встречу', 'relationship']):
        return random.choice(['Любовь ждет тебя за углом! ❤️', 'Сердце подсказывает - да! 💘', 'Встретишь свою половинку скоро! ✨'])
    
    elif any(word in question_lower for word in ['работа', 'job', 'карьер', 'career']):
        return random.choice(['Успех в работе близок! 💼', 'Новые возможности на горизонте! 🚀', 'Карьера пойдет вверх! 📈'])
    
    elif any(word in question_lower for word in ['деньги', 'money', 'богат', 'rich']):
        return random.choice(['Финансовый поток усиливается! 💰', 'Деньги идут к тебе! 🏦', 'Финансовая удача близка! 💸'])
    
    elif any(word in question_lower for word in ['здоровь', 'health', 'болезн']):
        return random.choice(['Здоровье будет крепким! 💪', 'Энергия переполняет тебя! ⚡', 'Тело благодарит за заботу! 🌿'])
    
    elif any(word in question_lower for word in ['путешеств', 'travel', 'отпуск']):
        return random.choice(['Новые горизонты ждут! ✈️', 'Приключения зовут! 🗺️', 'Открывай новые места! 🌍'])
    
    else:
        return random.choice(YES_NO_BASE)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(
        message.chat.id, 
        "🔮 *Привет! Я магический шар!*\n\nЗадай мне любой вопрос о будущем!", 
        parse_mode='Markdown', 
        reply_markup=get_keyboard()
    )

@bot.message_handler(commands=['model_test'])
def model_test(message):
    """Тест всех моделей"""
    bot.send_message(message.chat.id, "🔍 *Тестируем модели Hugging Face...*", parse_mode='Markdown')
    
    if not HF_API_TOKEN:
        bot.send_message(message.chat.id, "❌ Токен не установлен", parse_mode='Markdown')
        return
    
    results = test_alternative_models()
    bot.send_message(message.chat.id, f"🤖 *Результаты теста:*\n{results}", parse_mode='Markdown')

@bot.message_handler(commands=['smart_test'])
def smart_test(message):
    """Тест умных ответов"""
    test_questions = [
        "Я найду любовь?",
        "Будет ли у меня хорошая работа?",
        "Разбогатею ли я?",
        "Буду ли я здоров?"
    ]
    
    question = random.choice(test_questions)
    answer = get_simple_ai_response(question)
    
    bot.send_message(message.chat.id, f"🧪 *Тест умных ответов:*\n❓ {question}\n🤖 {answer}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    current_time = time.time()
    
    if user_id in user_locks and current_time - user_locks[user_id] < 10:
        remaining = int(10 - (current_time - user_locks[user_id]))
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} сек...", parse_mode='Markdown')
        return
    
    if message.text == '🚀 Отправить запрос в вселенную':
        question = "Что ждет меня в будущем?"
    else:
        question = message.text
    
    user_locks[user_id] = current_time
    
    bot.send_message(message.chat.id, "🔮 Трясу шар...", parse_mode='Markdown')
    time.sleep(2)
    
    # Используем умные ответы вместо Hugging Face
    answer = get_simple_ai_response(question)
    bot.send_message(message.chat.id, f"🔮 {answer}", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новым вопросам! 🚀", reply_markup=get_keyboard())

if __name__ == '__main__':
    print("🔮 Магический шар запущен!")
    print("🤖 Режим: Умные ответы (Hugging Face недоступен)")
    bot.polling(none_stop=True)
