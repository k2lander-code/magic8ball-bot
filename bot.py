from fastapi import FastAPI, Query
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ChatBot LLM")

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
# Проверенная рабочая модель через API Hugging Face
MODEL_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

@app.get("/")
def root():
    return {"status": "ok", "message": "Server is running on Render!"}

@app.get("/ping-hf")
def ping_huggingface():
    payload = {"inputs": "Привет, как дела?"}
    try:
        resp = requests.post(MODEL_URL, headers=headers, json=payload, timeout=20)
        if not resp.ok:
            return {
                "status": "error",
                "http_status": resp.status_code,
                "response_text": resp.text,
                "hint": "Проверьте MODEL_URL, HF_API_TOKEN и права доступа модели"
            }
        return {"status": "success", "huggingface_response": resp.json()}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

@app.get("/chat")
def chat(prompt: str = Query(..., description="Ваш текст для LLM")):
    """
    Эндпоинт /chat?prompt=Текст
    Возвращает ответ модели Hugging Face.
    """
    payload = {"inputs": prompt}
    try:
        resp = requests.post(MODEL_URL, headers=headers, json=payload, timeout=40)
        if not resp.ok:
            return {
                "status": "error",
                "http_status": resp.status_code,
                "response_text": resp.text,
                "hint": "Проверьте MODEL_URL, HF_API_TOKEN и права доступа модели"
            }
        data = resp.json()
        # Ответ модели в простом виде
        generated_text = data[0]["generated_text"] if isinstance(data, list) and "generated_text" in data[0] else str(data)
        return {"status": "success", "prompt": prompt, "response": generated_text}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
