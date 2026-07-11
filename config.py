"""Configuration module for DTDL Customer Intelligence Platform."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = BASE_DIR / "knowledge_base"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
VECTOR_STORE_DIR.mkdir(exist_ok=True)

# Application settings
APP_NAME = os.getenv("APP_NAME", "DTDL Customer Intelligence Platform")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Dashboard settings
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/dtdl_platform.db")

# NVIDIA API
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# LLM Model
LLM_MODEL = os.getenv("LLM_MODEL", "meta/llama-3.1-8b-instruct")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Agent settings
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# Intent categories
INTENT_CATEGORIES = [
    "billing",
    "technical",
    "retention",
    "sales",
    "escalation",
    "general"
]

# Escalation thresholds
ESCALATION_CONFIDENCE_THRESHOLD = 0.6
ESCALATION_SENTIMENT_THRESHOLD = -0.5
