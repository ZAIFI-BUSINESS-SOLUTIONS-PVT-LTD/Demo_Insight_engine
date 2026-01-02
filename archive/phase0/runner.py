import os
import shutil
import pandas as pd
import logging
from typing import Optional
from src.config import Config
from src.utils.logger import setup_logger
from .online_transformer import OnlineResponseTransformer
from .offline_transformer import OfflineResponseTransformer
from .answer_key_manager import AnswerKeyManager
from .sheet_extractor import SheetExtractor

logger = setup_logger(__name__)

class Phase0Runner:
    def __init__(self, target_class: Optional[str] = None):
        self.response_type = Config.RESPONSE_TYPE.upper()  # BOTH, ONLINE, OFFLINE

        # Shared input directories
        self.client_uploads_dir = Config.CLIENT_UPLOADS_DIR
        self.responses_dir = os.path.join(self.client_uploads_dir, "responses")
        self.online_shared_file = os.path.join(self.responses_dir, "Response_Online.xlsx")
        self.offline_shared_file = os.path.join(self.responses_dir, "Response_Offline.xlsx")

        # Allow passing target class via env var
        if target_class is None:
            target_class = os.getenv("TARGET_CLASS")

        if target_class and target_class != "None":
            self.classes_to_process = [target_class]
            logger.info(f"Processing only target class: {target_class}")
        else:
            available_sheets = set()
            if os.path.exists(self.online_shared_file):
                try:
                    xls_online = pd.ExcelFile(self.online_shared_file)
                    available_sheets.update(xls_online.sheet_names)
                except Exception:
                    pass
            if os.path.exists(self.offline_shared_file):
                try:
                    xls_offline = pd.ExcelFile(self.offline_shared_file)
                    available_sheets.update(xls_offline.sheet_names)
                except Exception:
                    pass
            self.classes_to_process = list(available_sheets)
            logger.info(f"Discovered classes from sheets: {self.classes_to_process}")


    def run(self):
        logger.info("=== Starting Phase 0 Execution ===")
        
        # Iterate classes
        # Iterate classes
        for cls in self.classes_to_process:
            try:
                self.process_class(cls)
                logger.info(f"✅ Class {cls} processed successfully.")
            except FileNotFoundError as e:
                if "QuestionPaper.pdf" in str(e):
                    logger.error(f"❌ Class {cls} FAILED: QuestionPaper.pdf not found in client_uploads.")
                else:
                    logger.error(f"❌ Class {cls} FAILED: {e}")
            except Exception as e:
                logger.error(f"❌ Class {cls} FAILED with unexpected error: {e}")

        logger.info("=== Phase 0 Execution Completed ===")

    def process_class(self, sheet_name_as_class_id: str):
        sheet_name = sheet_name_as_class_id
        folder_name = f"class_{sheet_name}"
        
        logger.info(f"--- Processing Sheet/Class: {sheet_name} (Folder: {folder_name}) ---")
        
        # Directories
        class_raw_dir = os.path.join(self.client_uploads_dir, folder_name)
        
        # EARLY CHECK: QuestionPaper.pdf
        # Strict rule: Class is skipped if PDF is missing.
        qp_src = os.path.join(class_raw_dir, "QuestionPaper.pdf")
        if not os.path.exists(qp_src):
             # Ensure we don't proceed. Raise FNF which works with the loop's try/except
             raise FileNotFoundError(f"QuestionPaper.pdf not found in {class_raw_dir}")

        class_norm_dir = os.path.join(Config.NORMALIZED_DIR, folder_name)
        class_phase1_dir = os.path.join(Config.INPUT_DIR, folder_name)
        
        # Ensure dirs exist
        os.makedirs(class_norm_dir, exist_ok=True)
        
        # 1. Sheet Extraction
        # Online
        online_extracted_path = os.path.join(class_norm_dir, "extracted_online_sheet.xlsx")
        has_online = False
        if self.response_type in ["ONLINE", "BOTH"]:
            if os.path.exists(self.online_shared_file):
                has_online = SheetExtractor.extract(self.online_shared_file, sheet_name, online_extracted_path)
            else:
                logger.warning(f"Shared Online Response file not found: {self.online_shared_file}")

        # Offline
        offline_extracted_path = os.path.join(class_norm_dir, "extracted_offline_sheet.xlsx")
        has_offline = False
        if self.response_type in ["OFFLINE", "BOTH"]:
            if os.path.exists(self.offline_shared_file):
                has_offline = SheetExtractor.extract(self.offline_shared_file, sheet_name, offline_extracted_path)
            else:
                 logger.warning(f"Shared Offline Response file not found: {self.offline_shared_file}")

        if not has_online and not has_offline:
            raise FileNotFoundError(
                f"Expected sheet '{sheet_name}' not found in response files."
            )
        
        # 2. Transformation (Build Matrix)
        response_matrices = []
        ak_manager = AnswerKeyManager()
        
        # Transform Online
        if has_online:
            try:
                t = OnlineResponseTransformer()
                df_online, key = t.transform(online_extracted_path, sheet_name) 
                response_matrices.append(df_online)
                if key: ak_manager.load_online_key(key)
            except Exception as e:
                logger.error(f"Online Transform Failed: {e}")
                raise e

        # Transform Offline
        if has_offline:
            try:
                 t = OfflineResponseTransformer()
                 df_offline, key = t.transform(offline_extracted_path, sheet_name)
                 response_matrices.append(df_offline)
                 if key: ak_manager.load_offline_key(key)
            except Exception as e:
                logger.error(f"Offline Transform Failed: {e}")
                raise e
        
        # Merge Matrices
        if not response_matrices:
             raise ValueError("No data generated.")
             
        # Concatenate along columns (axis=1) to combine student sets
        # Assumption: Online and Offline sets are distinct or compatible. 
        # We handle duplicates by keeping the first occurrence if overlap happens, or merge? 
        # Standard behaviour: concat
        
        final_matrix = pd.concat(response_matrices, axis=1)
        
        # Deduplicate columns (students) if any
        if final_matrix.columns.duplicated().any():
            logger.warning("Duplicate student IDs found across sources. Keeping first occurrence.")
            final_matrix = final_matrix.loc[:, ~final_matrix.columns.duplicated()]

        # Ensure Index is sorted/sequential 1..N
        # If concat introduced gaps (outer join), we fill keys with empty
        final_matrix = final_matrix.sort_index()
        final_matrix = final_matrix.fillna("")
        
        # 3. Validate Matrix Structure
        self.validate_matrix(final_matrix)
        
        # Resolve Key
        ak_manager.resolve()
        
        # Write Artifacts
        resp_csv_path = os.path.join(class_norm_dir, "ResponseSheet.csv")
        ak_json_path = os.path.join(class_norm_dir, "answer_key.json")
        audit_path = os.path.join(class_norm_dir, "answer_key_comparison_report.csv")
        
        # Write Matrix Directly
        final_matrix.to_csv(resp_csv_path) # Index (question_id) is written as Col A
        ak_manager.save_key_json(ak_json_path)
        ak_manager.generate_report(audit_path)
        
        # Publish to Phase 1 Input
        os.makedirs(class_phase1_dir, exist_ok=True)
        
        # Guardrail: Clean .xlsx from input/
        self.clean_input_dir(class_phase1_dir)
        
        shutil.copy2(resp_csv_path, os.path.join(class_phase1_dir, "ResponseSheet.csv"))
        shutil.copy2(ak_json_path, os.path.join(class_phase1_dir, "answer_key.json"))
        
        # Copy QuestionPaper.pdf
        qp_src = os.path.join(class_raw_dir, "QuestionPaper.pdf")
        if os.path.exists(qp_src):
            shutil.copy2(qp_src, os.path.join(class_phase1_dir, "QuestionPaper.pdf"))
        else:
            raise FileNotFoundError(f"Missing QuestionPaper.pdf in {class_raw_dir}")

        # Copy Solutions.pdf (Optional but recommended)
        # We check for "Solution.pdf" or "Solutions.pdf" and normalize to "Solutions.pdf"
        sol_candidates = ["Solutions.pdf", "Solution.pdf"]
        found_sol = False
        for cand in sol_candidates:
            sol_src = os.path.join(class_raw_dir, cand)
            if os.path.exists(sol_src):
                shutil.copy2(sol_src, os.path.join(class_phase1_dir, "Solutions.pdf"))
                logger.info(f"Copied {cand} to input as Solutions.pdf")
                found_sol = True
                break
        
        if not found_sol:
            logger.info("No Solution PDF found (optional).")

        logger.info(f"Class/Sheet {sheet_name} processed successfully.")

    def clean_input_dir(self, directory: str):
        # Remove any .xlsx files to satisfy Phase 1 strictness
        for f in os.listdir(directory):
            if f.endswith(".xlsx"):
                os.remove(os.path.join(directory, f))
                logger.warning(f"Removed illegal .xlsx file from Phase 1 input: {f}")

    def validate_matrix(self, df: pd.DataFrame):
        """
        Validates the Question x Student Matrix structure.
        """
        # 1. A1 must be question_id (Index Name)
        if df.index.name != "question_id":
             raise ValueError("Matrix Validation Failed: Index name must be 'question_id'")
        
        # 2. Sequential Numbering 1..N
        expected_index = pd.Index(range(1, len(df) + 1), name="question_id")
        if not df.index.equals(expected_index):
             # Check if it's just missing some or unordered?
             # We sorted it. If it doesn't match range, there are gaps or start!=1
             raise ValueError(f"Matrix Validation Failed: Question IDs must be sequential 1..N. Found: {df.index.tolist()}")

        # 3. Student IDs (Columns) must be unique
        if df.columns.duplicated().any():
             # Should be handled by merge logic, but double check
             raise ValueError("Matrix Validation Failed: Duplicate Student IDs in columns.")
        
        # 4. Values must be A/B/C/D or empty
        # Flatten and check unique
        unique_vals = pd.unique(df.values.ravel())
        valid_set = {'A', 'B', 'C', 'D', ''}
        
        for v in unique_vals:
            if str(v) not in valid_set:
                 # Check strictness: "Matrix cells must be A/B/C/D or empty"
                 # If we have "a" or "b", transformers should have normalized.
                 # If we have "N/A" or "0", it's invalid.
                 raise ValueError(f"Matrix Validation Failed: Invalid cell value found '{v}'. Allowed: A, B, C, D, empty string.")


def process():
    # Detect target?
    target = os.getenv("TARGET_CLASS") # Optional specific target
    runner = Phase0Runner(target if target and target != "None" else None)
    runner.run()
