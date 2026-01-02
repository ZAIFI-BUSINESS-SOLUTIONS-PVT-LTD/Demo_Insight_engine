"""
Helper script to convert answer_key.json to answer_key.csv format
"""
import os
import json
import pandas as pd
from src.config import Config

def convert_answer_key(class_name):
    input_dir = os.path.join(Config.INPUT_DIR, class_name)
    json_path = os.path.join(input_dir, "answer_key.json")
    csv_path = os.path.join(input_dir, "answer_key.csv")
    
    if not os.path.exists(json_path):
        print(f"Skipping {class_name}: answer_key.json not found")
        return
    
    # Read JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Convert to CSV format
    rows = []
    for item in data:
        rows.append({
            'question_id': item['question_id'],
            'Answer': item['correct_option']
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    print(f"✓ Converted {class_name}/answer_key.json to CSV")

def main():
    if not os.path.exists(Config.INPUT_DIR):
        print(f"Input directory not found: {Config.INPUT_DIR}")
        return
    
    classes = [d for d in os.listdir(Config.INPUT_DIR) 
               if os.path.isdir(os.path.join(Config.INPUT_DIR, d))]
    
    print(f"Found {len(classes)} classes")
    for cls in classes:
        convert_answer_key(cls)
    
    print("\nConversion complete!")

if __name__ == "__main__":
    main()
