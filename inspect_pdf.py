from src.utils.pdf_loader import load_pdf_pages
from src.config import Config
import os

Config.INPUT_DIR = "d:/ZAi-Fi/06. My Tech Projects/05_Pace/pace_analytics/input"

def inspect():
    path = os.path.join(Config.INPUT_DIR, "class_engineering", "QuestionPaper.pdf")
    print(f"Inspecting {path}")
    for page, text in load_pdf_pages(path):
        print(f"--- PAGE {page} ---")
        print(text[:500]) # First 500 chars
        print("...")

if __name__ == "__main__":
    inspect()
