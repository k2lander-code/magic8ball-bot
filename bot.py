import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import random
import os
import requests

# Переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')  # Твой токен test4

# Проверка токенов
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не установлен")
    exit(1)

if not HF_API_TOKEN:
    print("⚠️ HF_API_TOKEN не установлен - будем использовать только случайные ответы")

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
    """Предсказание через Hugging Face Inference API"""
    if not HF_API_TOKEN:
        return random.choice(YES_NO_BASE)
    
    try:
        # Используем DialoGPT-medium - хорош для диалогов
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        # Промпт для магического шара
        prompt = f"Ты - магический шар предсказаний. Ответь кратко и мистически на вопрос: '{question}'. Ответ должен быть не более 15 слов."
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 80,
                "temperature": 0.9,
                "do_sample": True,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True  # Ждем если модель загружается
            }
        }
        
        print(f"🔄 Отправляем запрос в Hugging Face: {question[:30]}...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Hugging Face ответ: {result}")
            
            if isinstance(result, list) and len(result) > 0:
                answer = result[0]['generated_text'].strip()
                # Убираем повторения промпта если есть
                if prompt in answer:
                    answer = answer.replace(prompt, '').strip()
                return answer if answer else random.choice(YES_NO_BASE)
            else:
                return random.choice(YES_NO_BASE)
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
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
    
    # Проверка таймаута
    if user_id in user_locks and current_time - user_locks[user_id] < 10:
        remaining = int(10 - (current_time - user_locks[user_id]))
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} сек...", parse_mode='Markdown')
        return
    
    # Определяем вопрос
    question = "Что шепнёт вселенная сегодня?" if message.text == '🚀 Отправить запрос в вселенную' else message.text
    
    user_locks[user_id] = current_time
    
    # Трясем шар
    bot.send_message(message.chat.id, "🔮 Трясём шар... Ш-ш-ш...", parse_mode='Markdown')
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
    bot.send_message(message.chat.id, f"🔮 *{answer}*", parse_mode='Markdown')
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новому вопросу! 🚀", reply_markup=get_keyboard())

if __name__ == '__main__':
    print("🔮 Магический шар запущен!")
    print(f"🤖 Hugging Face: {'✅ Доступен' if HF_API_TOKEN else '❌ Не настроен'}")
    bot.polling(none_stop=True)
