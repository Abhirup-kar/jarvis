import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "JARVIS Assistant"
    HOST: str = os.getenv("JARVIS_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("JARVIS_PORT", "8000"))
    WS_PORT: int = int(os.getenv("JARVIS_WS_PORT", "8765"))
    
    # Model configs (Supports OpenAI, Groq, OpenRouter, Ollama, LocalAI)
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Audio configs
    SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", "16000"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1024"))
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-GB-RyanNeural")  # British accent for JARVIS
    WAKE_WORD: str = os.getenv("WAKE_WORD", "hey_jarvis")
    
    # Vision configs
    CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))
    PINCH_THRESHOLD: float = float(os.getenv("PINCH_THRESHOLD", "0.04"))
    
    # Paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    CONFIG_DIR: Path = BASE_DIR / "config"

settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
(settings.STORAGE_DIR / "sqlite").mkdir(parents=True, exist_ok=True)
(settings.STORAGE_DIR / "logs").mkdir(parents=True, exist_ok=True)