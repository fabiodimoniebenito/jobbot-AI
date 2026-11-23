"""Configuración: rutas y variables de entorno. Los datos generados viven en data/."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / ".env")

CV_FILE = Path(os.getenv("CV_FILE", BASE / "cv_base.json"))
TEMPLATE_DIR = BASE / "plantilla"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()  # "anthropic" | "ollama"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))  # el valor por defecto de Ollama trunca ofertas largas
_DEF_MODEL, _DEF_SCORE = (("qwen2.5:14b", "qwen2.5:7b") if LLM_PROVIDER == "ollama"
                          else ("claude-sonnet-5-5", "claude-haiku-5-5"))
MODEL = os.getenv("CLAUDE_MODEL", _DEF_MODEL)  # carta y CV (calidad de redacción)
SCORE_MODEL = os.getenv("SCORE_MODEL", _DEF_SCORE)  # extracción y puntuación (barato)
MIN_SCORE = int(os.getenv("MIN_SCORE", "65"))

DATA_DIR = BASE / "data"
OUT_DIR = DATA_DIR / "salidas"
PENDING_FILE = DATA_DIR / "pendientes.json"
SEEN_FILE = DATA_DIR / "vistas.json"
LOG_FILE = DATA_DIR / "registro.csv"
OFFERS_FILE = DATA_DIR / "ofertas.json"
OFFERS_HTML = DATA_DIR / "ofertas.html"
