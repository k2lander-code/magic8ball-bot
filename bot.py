from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
MODEL_URL = "https://api-inference.huggingface.co/models/gpt2"  # можно заменить на свой

@app.get("/")
def root():
    return {"status": "ok", "message": "Server is running on Render!"}

@app.get("/ping-hf")
def ping_huggingface():
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": "Привет, как дела?"}

    try:
        response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {"status": "success", "huggingface_response": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
