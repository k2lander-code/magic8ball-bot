import telebot
import time
import random
import requests
import os
import threading
from flask import Flask

# === Переменные окружения (Render Environment Variables) ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# === Настройки Hugging Face ===
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3-8b-instruct"
headers = lambda: {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

def get_huggingface_response(prompt):
    try:
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 80}}
        response = requests.post(API_URL, headers=headers(), json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data[0]["generated_text"].strip()
        return f"⚠️ Ошибка Hugging Face: {response.status_code}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

# === Запасной вариант (если Hugging Face не отвечает) ===
def get_simple_ai_response(question):
    responses = [
        "Судьба хранит свои тайны...",
        "Будущее готовит тебе приятный сюрприз!",
        "Все возможно, если ты веришь!"
    ]
    return random.choice(responses)

# === Telegram-бот ===
user_locks = {}

def get_keyboard():
    from telebot import types
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("🚀 Отправить запрос в вселенную"))
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔮 Привет! Я магический шар с интеллектом!", parse_mode='Markdown')
    question = random.choice([
        "Что такое искусственный интеллект?",
        "Когда появится жизнь на Марсе?",
        "Что ждет меня в будущем?"
    ])
    answer = get_huggingface_response(question)
    bot.send_message(message.chat.id, f"❓ {question}\n🤖 {answer}", parse_mode='Markdown', reply_markup=get_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    current_time = time.time()
    if user_id in user_locks and current_time - user_locks[user_id] < 10:
        remaining = int(10 - (current_time - user_locks[user_id]))
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} сек...", parse_mode='Markdown')
        return

    user_locks[user_id] = current_time
    question = "Что ждет меня в будущем?" if message.text == '🚀 Отправить запрос в вселенную' else message.text

    bot.send_message(message.chat.id, "🔮 Трясу шар...", parse_mode='Markdown')
    time.sleep(2)

    answer = get_huggingface_response(question)
    if "Ошибка" in answer:
        answer = get_simple_ai_response(question)

    bot.send_message(message.chat.id, f"🔮 {answer}", parse_mode='Markdown')
    bot.send_message(message.chat.id, "Готов к новым вопросам! 🚀", reply_markup=get_keyboard())

# === Flask веб-сервер (чтобы Render не засыпал) ===
@app.route('/')
def home():
    return "🤖 Telegram Bot is running on Render!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

def run_telegram():
    bot.infinity_polling(timeout=60, long_polling_timeout=30)

if __name__ == '__main__':
    print("🚀 Запуск Flask и Telegram бота...")
    threading.Thread(target=run_telegram).start()
    run_flask()
