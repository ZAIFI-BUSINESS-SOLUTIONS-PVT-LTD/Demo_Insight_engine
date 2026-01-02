import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.0-flash")
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, "input")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    # Defaults
    DEFAULT_CLASS = os.getenv("TARGET_CLASS", "class_medical")
    
    # Validation Rules
    # Phase 0 Config
    RESPONSE_TYPE = os.getenv("RESPONSE_TYPE", "BOTH") # ONLINE, OFFLINE, BOTH
    
    CLIENT_UPLOADS_DIR = os.path.join(BASE_DIR, "client_uploads")
    NORMALIZED_DIR = os.path.join(BASE_DIR, "normalized_inputs")
