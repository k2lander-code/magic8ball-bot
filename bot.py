import os
from openai import OpenAI

# Установи токен Hugging Face
os.environ["HF_TOKEN"] = "hf_ВАШ_ТОКЕН"

# Создаём клиент OpenAI, но через Hugging Face Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"]
)

# Модель
MODEL_NAME = "swiss-ai/Apertus-8B-Instruct-2509:publicai"

# Вопрос
prompt = "Сколько планет в Солнечной системе и какие, кратко до 20 слов."

# Отправка запроса
completion = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": prompt}]
)

# Получаем текст ответа
answer = completion.choices[0].message["content"]

# Выводим в консоль
print("Ответ модели:")
print(answer)
