"""Utility functions for DTDL Customer Intelligence Platform."""
import uuid
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Configure logging
def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log")
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def generate_ticket_id() -> str:
    """Generate a unique ticket ID."""
    return f"DTDL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def generate_customer_id() -> str:
    """Generate a unique customer ID."""
    return f"CUST-{uuid.uuid4().hex[:8].upper()}"

def clean_phone_number(phone: str) -> str:
    """Clean and format phone number."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"+91-{digits[:5]}-{digits[5:]}"
    return phone

def calculate_sentiment(text: str) -> float:
    """Simple sentiment analysis (placeholder for ML model)."""
    positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'love', 'best', 'perfect', 'amazing', 'thank']
    negative_words = ['bad', 'terrible', 'worst', 'hate', 'angry', 'frustrated', 'disappointed', 'slow', 'broken', 'issue', 'problem', 'complaint']

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total

def format_response_time(minutes: float) -> str:
    """Format response time in human-readable format."""
    if minutes < 1:
        return f"{int(minutes * 60)}s"
    elif minutes < 60:
        return f"{int(minutes)}m"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m"

def safe_json_loads(data: Any) -> Dict[str, Any]:
    """Safely parse JSON string."""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def sanitize_input(text: str) -> str:
    """Sanitize user input."""
    # Remove potentially harmful characters
    text = re.sub(r'[<>{}/\\]', '', text)
    return text.strip()
