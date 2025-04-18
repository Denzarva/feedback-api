
import os
import logging
import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("feedback_app")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed request: {request.method} {request.url} - Status code: {response.status_code}")
    return response

@app.get("/ping")
async def ping():
    return {"message": "pong"}

class Feedback(BaseModel):
    feedback: str

def analyze_feedback_with_gpt(feedback_text: str):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": (
                    "Ты — AI-ассистент, который анализирует обратную связь клиентов. "
                    "Кратко подведи итоги и оцени тональность: позитивная, нейтральная или негативная. "
                    "Формат ответа:\nsummary: <краткое резюме>\nsentiment: <тональность>"
                )},
                {"role": "user", "content": feedback_text}
            ]
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        gpt_reply = response.json()["choices"][0]["message"]["content"]

        summary, sentiment = "N/A", "unknown"
        for line in gpt_reply.splitlines():
            if line.lower().startswith("summary:"):
                summary = line.split(":", 1)[-1].strip()
            elif line.lower().startswith("sentiment:"):
                sentiment = line.split(":", 1)[-1].strip()

        return summary, sentiment

    except Exception as e:
        logger.error(f"GPT analysis failed: {e}")
        return "Analysis unavailable", "unknown"

@app.post("/feedback")
async def save_feedback(item: Feedback):
    try:
        with open("feedback.txt", "a", encoding="utf-8") as f:
            f.write(item.feedback + "\n")
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    summary, sentiment = analyze_feedback_with_gpt(item.feedback)

    return {
        "message": "Feedback saved",
        "summary": summary,
        "sentiment": sentiment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
