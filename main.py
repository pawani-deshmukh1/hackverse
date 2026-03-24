from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from routes.analyze import router as analyze_router
from routes.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("audioauth")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎙️  AudioAuth API starting up...")
    logger.info("Primary  : Gemini API")
    logger.info("Fallback : Ollama (llama3.1)")
    yield
    logger.info("AudioAuth API shutting down.")


app = FastAPI(
    title="AudioAuth API",
    description="AI vs Human voice classification engine — supports Tamil, English, Hindi, Malayalam, Telugu",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(health_router, prefix="/api/v1", tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "AudioAuth API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "health":  "GET  /api/v1/health",
            "models":  "GET  /api/v1/models",
        }
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
