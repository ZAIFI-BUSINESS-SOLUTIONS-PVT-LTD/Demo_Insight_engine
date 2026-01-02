import os
import json
import pandas as pd
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AnswerKeyManager:
    """
    Manages Answer Key resolution with strict authority rules.
    """
    
    def __init__(self):
        self.offline_key: Dict[int, str] = {}
        self.online_key: Dict[int, str] = {}
        self.solution_key: Dict[int, str] = {}
        self.authoritative_key: Dict[int, str] = {}
        self.source_used = "NONE"

    def load_offline_key(self, key: Dict[int, str]):
        self.offline_key = key
    
    def load_online_key(self, key: Dict[int, str]):
        self.online_key = key
        
    def load_solution_key(self, solution_file_path: str):
        """
        Loads solution key from extracted solution.json (Phase 1 artifact).
        We assume this file is available or we trigger extraction?
        For Phase 0 isolation, we likely rely on reading an existing file or skipping.
        If file doesn't exist, we skip.
        """
        if not os.path.exists(solution_file_path):
            logger.warning(f"Solution file not found: {solution_file_path}. Skipping solution key.")
            return

        try:
            with open(solution_file_path, 'r') as f:
                data = json.load(f)
                # List of {question_id, correct_option, ...}
                for item in data:
                    q_id = item.get("question_id")
                    opt = item.get("correct_option")
                    if q_id and opt:
                        self.solution_key[int(q_id)] = opt
        except Exception as e:
            logger.error(f"Failed to load solution key: {e}")

    def resolve(self) -> Dict[int, str]:
        """
        Applies Authority Decision Rules.
        Returns final key.
        """
        # Determine strict set of common questions? Or Union?
        # Usually keys should cover all questions.
        
        all_q_ids = set(self.offline_key.keys()) | set(self.online_key.keys()) | set(self.solution_key.keys())
        if not all_q_ids:
            return {} # Or raise? If no data, we can't produce a key. But maybe we produce empty key?
            # If validated schema ensures data, we should have keys if we have data.
            # But duplicate check logic in transformer might result in empty key if format wrong?
            # Raise for safety.
            raise ValueError("No answer keys extracted.")

        # Rule 0: Single Source Authority
        if self.offline_key and not self.online_key:
            logger.info("Only Offline Key found. Using as authoritative.")
            self.authoritative_key = self.offline_key
            self.source_used = "OFFLINE"
            return self.authoritative_key
            
        if self.online_key and not self.offline_key:
            logger.info("Only Online Key found. Using as authoritative.")
            self.authoritative_key = self.online_key
            self.source_used = "ONLINE"
            return self.authoritative_key

        # Rule 1: Offline vs Online matches >= 95%
        if self.offline_key and self.online_key:
             match_count = 0
             common_count = 0
             for q in all_q_ids:
                 v1 = self.offline_key.get(q)
                 v2 = self.online_key.get(q)
                 if v1 and v2:
                     common_count += 1
                     if v1 == v2:
                         match_count += 1
             
             if common_count > 0:
                 accuracy = match_count / common_count
                 logger.info(f"Offline vs Online Agreement: {accuracy:.2%}")
                 
                 if accuracy >= 0.95:
                     self.authoritative_key = self.offline_key
                     self.source_used = "OFFLINE"
                     return self.authoritative_key
                 else:
                     logger.warning("Offline vs Online mismatch > 5%. Checking next rule.")

        # Rule 2: Online vs Solution matches >= 95%
        if self.online_key and self.solution_key:
             match_count = 0
             common_count = 0
             for q in all_q_ids:
                 v1 = self.online_key.get(q)
                 v2 = self.solution_key.get(q)
                 if v1 and v2:
                     common_count += 1
                     if v1 == v2:
                         match_count += 1
             
             if common_count > 0:
                 accuracy = match_count / common_count
                 logger.info(f"Online vs Solution Agreement: {accuracy:.2%}")
                 
                 if accuracy >= 0.95:
                     self.authoritative_key = self.online_key
                     self.source_used = "ONLINE"
                     return self.authoritative_key

        # Rule 3: Solution Exists (and others missing/inconsistent)
        if self.solution_key:
            logger.info("Fallback to Solution Key.")
            self.authoritative_key = self.solution_key
            self.source_used = "SOLUTION"
            return self.authoritative_key
        
        # Rule 4: Fail
        raise ValueError(
            "Answer Key Resolution Failed: No authoritative source satisfied the 95% rule."
        )


    def generate_report(self, output_path: str):
        rows = []
        all_q_ids = sorted(list(set(self.offline_key.keys()) | set(self.online_key.keys()) | set(self.solution_key.keys())))
        
        for q in all_q_ids:
            rows.append({
                "question_id": q,
                "offline_key": self.offline_key.get(q, ""),
                "online_key": self.online_key.get(q, ""),
                "solution_key": self.solution_key.get(q, ""),
                "final_key": self.authoritative_key.get(q, ""),
                "match": (self.authoritative_key.get(q) == self.solution_key.get(q)) if self.solution_key.get(q) else "N/A"
            })
            
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        logger.info(f"Audit report saved to {output_path}")

    def save_key_json(self, output_path: str):
         # Convert Dict to List for Phase 1/Standard JSON
         # Format: [{"question_id": 1, "correct_option": "A"}, ...]
         # Or does Phase 1 expect simple list? 
         # Phase 1 merges `solution.json`. It expects `solution.json` to have `correct_option`.
         # But here we are generating `answer_key.json`.
         # Phase 1 reads `solution.json` (extracted from PDF). 
         # If Phase 0 provides authoritative key, Phase 1 should use it?
         # "Phase 0... Generate answer_key.json". 
         # "Phase 1... Consumes ... Solutions.pdf OR answer_key.json"
         
         data = []
         for q, opt in sorted(self.authoritative_key.items()):
             data.append({
                 "question_id": q,
                 "correct_option": opt
             })
         
         with open(output_path, 'w') as f:
             json.dump(data, f, indent=4)
             
         logger.info(f"Answer Key JSON saved to {output_path}")
