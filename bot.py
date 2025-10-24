import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import random
import os
import requests

# Настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не установлен")
    exit(1)

print("🔮 Запускаем магический шар...")
print(f"🤖 Hugging Face: {'✅ Настроен' if HF_API_TOKEN else '❌ Не настроен'}")

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

def test_huggingface_detailed():
    """Детальный тест Hugging Face"""
    if not HF_API_TOKEN:
        return "❌ Токен не установлен"
    
    try:
        API_URL = "https://api-inference.huggingface.co/models/gpt2"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        payload = {
            "inputs": "Say hello",
            "parameters": {"max_length": 10}
        }
        
        print("🔍 Тестируем Hugging Face API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📡 HTTP статус: {response.status_code}")
        print(f"📄 Ответ: {response.text[:200]}")
        
        if response.status_code == 200:
            result = response.json()
            return f"✅ API работает! Ответ: {result}"
        elif response.status_code == 401:
            return "❌ Ошибка 401: Неверный токен API"
        elif response.status_code == 404:
            return "❌ Ошибка 404: Модель не найдена"
        elif response.status_code == 503:
            return "🔄 Модель загружается... Попробуй через 1-2 минуты"
        else:
            return f"❌ Ошибка {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"❌ Исключение: {str(e)}"

def get_ai_prediction(question):
    """Функция для AI с логированием"""
    if not HF_API_TOKEN:
        print("❌ HF_API_TOKEN не установлен")
        return random.choice(YES_NO_BASE)
    
    try:
        API_URL = "https://api-inference.huggingface.co/models/gpt2"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        prompt = f"Q: {question} A:"
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 50, "temperature": 0.8}
        }
        
        print(f"🔄 Отправляем запрос: '{question}'")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📡 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Raw ответ: {result}")
            
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                if prompt in answer:
                    answer = answer.replace(prompt, '').strip()
                if answer and len(answer) > 3:
                    print(f"✅ AI ответил: '{answer}'")
                    return answer
        
        print("❌ AI не сработал, используем случайный ответ")
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
        "🔮 *Привет! Я магический шар!*\n\nИспользуй /diagnostic для проверки AI", 
        parse_mode='Markdown', 
        reply_markup=get_keyboard()
    )

@bot.message_handler(commands=['diagnostic'])
def diagnostic(message):
    """Полная диагностика"""
    bot.send_message(message.chat.id, "🔧 *Запускаем диагностику...*", parse_mode='Markdown')
    
    # Проверяем токен
    token_status = "✅ Токен установлен" if HF_API_TOKEN else "❌ Токен отсутствует"
    
    # Тестируем API
    api_status = test_huggingface_detailed()
    
    diagnostic_info = f"""
🔧 *ДИАГНОСТИКА AI:*

*Токен Hugging Face:*
{token_status}

*API статус:*
{api_status}

*Рекомендации:*
1. Проверь HF_API_TOKEN в настройках Render
2. Убедись что токен активен в Hugging Face
3. Попробуй создать новый токен
    """
    
    bot.send_message(message.chat.id, diagnostic_info, parse_mode='Markdown')

@bot.message_handler(commands=['test'])
def test(message):
    """Тест AI"""
    bot.send_message(message.chat.id, "🧪 *Тестируем AI...*", parse_mode='Markdown')
    
    answer = get_ai_prediction("Will I be happy?")
    
    if answer in YES_NO_BASE:
        bot.send_message(message.chat.id, f"❌ AI не работает\n🤖 Ответ: {answer}", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"✅ AI РАБОТАЕТ!\n🤖 Ответ: {answer}", parse_mode='Markdown')

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
    
    bot.send_message(message.chat.id, "🔮 Думаю...", parse_mode='Markdown')
    time.sleep(1)
    
    answer = get_ai_prediction(question)
    bot.send_message(message.chat.id, f"🔮 {answer}", parse_mode='Markdown')

if __name__ == '__main__':
    print("✅ Бот запущен! Ожидаем сообщения...")
    bot.polling(none_stop=True)
