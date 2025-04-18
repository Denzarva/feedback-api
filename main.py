import logging
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
    """Middleware to log all incoming requests and responses"""
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(
        f"Completed request: {request.method} {request.url} - Status code: {response.status_code}"
    )
    return response

@app.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"message": "pong"}

class Feedback(BaseModel):
    feedback: str

@app.post("/feedback")
async def save_feedback(item: Feedback):
    """Endpoint to receive feedback and save it to feedback.txt"""
    try:
        with open("feedback.txt", "a", encoding="utf-8") as f:
            f.write(item.feedback + "\n")
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return {"message": "Feedback saved"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=True
    )