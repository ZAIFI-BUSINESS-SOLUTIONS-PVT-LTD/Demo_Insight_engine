import google.generativeai as genai
import os
import json
import logging
import re
from src.config import Config

logger = logging.getLogger(__name__)

def setup_gemini():
    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=Config.GEMINI_API_KEY)

def safe_json_loads(text: str):
    """
    Attempt to load JSON, fixing common issues like stray backslashes, raw newlines, and trailing commas.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        fixed_text = text
        
        # 1. Fix raw newlines: Replace unescaped newlines with escaped ones.
        fixed_text = re.sub(r'(?<!\\)\n', r'\\n', fixed_text)
        
        # 2. Fix stray backslashes: Escape backslashes that are not part of a valid JSON escape sequence.
        # regex finds a backslash not followed by one of the valid JSON escape chars (", \, /, b, f, n, r, t)
        # or a unicode escape (\uXXXX).
        # It also handles cases where a backslash might be at the end of the string or before a non-escape char.
        fixed_text = re.sub(r'\\(?![\\"\/bfnrtu])', r'\\\\', fixed_text)
        
        # 3. Fix trailing commas in objects and arrays
        # This regex finds a comma followed by optional whitespace and then a closing brace or bracket.
        fixed_text = re.sub(r',\s*([}\]])', r'\1', fixed_text)

        try:
            return json.loads(fixed_text)
        except Exception:
            # This regex finds a comma followed by optional whitespace and then a closing brace or bracket.
            fixed_text = re.sub(r',\s*([}\]])', r'\1', fixed_text)

            try:
                return json.loads(fixed_text)
            except Exception:
                # If still failing, raise original error for visibility
                raise e

def call_gemini_json(prompt: str, content: str) -> dict | list:
    """
    Calls Gemini with a prompt and content, expecting a JSON response.
    """
    model = genai.GenerativeModel(Config.MODEL_NAME)
    
    full_prompt = f"{prompt}\n\nCONTENT:\n{content}"
    
    try:
        response = model.generate_content(full_prompt)
        text = response.text
        
        # Clean up markdown code blocks
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        return safe_json_loads(text)
    except Exception as e:
        logger.error(f"Error calling Gemini or parsing JSON: {e}")
        logger.error(f"Raw response: {text if 'text' in locals() else 'No response'}")
        raise

def call_gemini_text(prompt: str, content: str) -> str:
    """
    Calls Gemini with a prompt and content, returning raw text response.
    """
    model = genai.GenerativeModel(Config.MODEL_NAME)
    
    full_prompt = f"{prompt}\n\nCONTENT:\n{content}"
    
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error calling Gemini (Text Mode): {e}")
        raise


