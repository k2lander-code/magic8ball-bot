import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI
import time
import random
import os

# ТОЛЬКО из переменных окружения - без fallback значений!
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)
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

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_locks[user_id] = 0
    bot.send_message(message.chat.id, 
                     "🔮 *Привет, искатель тайн!*\nСпроси что угодно — я дам предсказание из шара.\nНажми кнопку или напиши вопрос.", 
                     parse_mode='Markdown', reply_markup=get_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if user_id in user_locks and time.time() - user_locks[user_id] < 10:
        bot.send_message(message.chat.id, "⏳ *Подожди, вселенная ещё думает... Не торопи судьбу!*" , parse_mode='Markdown')
        return
    
    if message.text == '🚀 Отправить запрос в вселенную':
        question = "Что шепнёт вселенная сегодня?"
    else:
        question = message.text
    
    user_locks[user_id] = time.time()
    
    bot.send_message(message.chat.id, "🔮 *Трясём шар... Держись! Ш-ш-ш...* 🔮", parse_mode='Markdown')
    time.sleep(2)
    
    word_count = len(question.split())
    if word_count <= 7 and random.random() > 0.3:
        answer = random.choice(YES_NO_BASE)
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Ты — мистический шар предсказаний. Дай короткий, юмористический ответ до 25 слов на: '{question}'. Сделай как предсказание судьбы."}]
            )
            full_answer = response.choices[0].message.content.strip()
            answer = full_answer[:25] + "..." if len(full_answer) > 25 else full_answer
        except Exception as e:
            answer = "Вселенная молчит... Попробуй позже. 🔮"
    
    words = answer.split()
    if len(words) <= 7:
        bot.send_message(message.chat.id, f"🔮 *{answer}* 🔮", parse_mode='Markdown')
    else:
        for i in range(0, len(words), 7):
            chunk = ' '.join(words[i:i+7])
            bot.send_message(message.chat.id, f"🔮 *{chunk}* 🔮", parse_mode='Markdown')
            if i + 7 < len(words):
                time.sleep(5)
    
    time.sleep(1)
    bot.send_message(message.chat.id, "Готов к новому вопросу! 🚀", reply_markup=get_keyboard())

if __name__ == '__main__':
    while True:
        try:
            print("Бот запущен! Нажми Ctrl+C для остановки.")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(15)
