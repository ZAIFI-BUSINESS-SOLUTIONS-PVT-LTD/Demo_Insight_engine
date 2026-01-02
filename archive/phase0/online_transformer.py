import pandas as pd
import logging
from typing import Tuple, Dict
from src.phase0.interface import ResponseTransformer

logger = logging.getLogger(__name__)


class OnlineResponseTransformer(ResponseTransformer):

    # =============================
    # HARD-CONTRACTED COLUMN LAYOUT
    # =============================
    STUDENT_ID_COL = 0   # Column A → RollNo
    FIRST_Q_COL = 9      # Column J → First question response
    Q_COL_STEP = 2       # J, L, N, ...

    def transform(self, input_path: str, target_class: str) -> Tuple[pd.DataFrame, Dict[int, str]]:
        logger.info(f"Processing Online Format (Hardcoded Columns): {input_path} for class {target_class}")

        xls = pd.ExcelFile(input_path)

        students_dict: Dict[str, Dict[int, str]] = {}
        extracted_key: Dict[int, str] = {}

        max_q_id_found = 0
        processed_sheets = 0

        for sheet_name in xls.sheet_names:
            if target_class.lower() not in sheet_name.lower():
                continue

            processed_sheets += 1
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # =====================================
            # STEP 1: DETECT HEADER ROW (RollNo row)
            # =====================================
            header_row_idx = None

            for idx, row in df.iterrows():
                first_cell = str(row.iloc[self.STUDENT_ID_COL]).strip().upper()
                if first_cell == "ROLLNO":
                    header_row_idx = idx
                    break

            if header_row_idx is None:
                raise ValueError(
                    f"[ONLINE FORMAT ERROR] Could not locate header row with 'RollNo' in sheet '{sheet_name}'"
                )

            header = df.iloc[header_row_idx]
            data_start_row_idx = header_row_idx + 1

            # =====================================
            # STEP 2: VALIDATE FIRST QUESTION COLUMN
            # =====================================
            if self.FIRST_Q_COL >= len(header):
                raise ValueError(
                    f"[ONLINE FORMAT ERROR] Expected first question at column J "
                    f"but sheet '{sheet_name}' has only {len(header)} columns"
                )

            first_q_header = str(header.iloc[self.FIRST_Q_COL]).strip().upper()
            if not first_q_header or first_q_header == "NAN":
                raise ValueError(
                    f"[ONLINE FORMAT ERROR] Column J does not contain question data in sheet '{sheet_name}'"
                )

            # =====================================
            # STEP 3: BUILD QUESTION COLUMN MAP
            # =====================================
            col_map = {}
            local_q = 1
            q_col = self.FIRST_Q_COL

            while q_col < len(header):
                col_header = str(header.iloc[q_col]).strip()
                if not col_header or col_header.lower() == "nan":
                    break

                col_map[local_q] = q_col
                q_col += self.Q_COL_STEP
                local_q += 1

            if not col_map:
                raise ValueError(
                    f"[ONLINE FORMAT ERROR] No question columns detected starting from column J in sheet '{sheet_name}'"
                )

            # =====================================
            # STEP 4: READ STUDENT RESPONSES
            # =====================================
            for r_idx in range(data_start_row_idx, len(df)):
                row = df.iloc[r_idx]
                student_id = row.iloc[self.STUDENT_ID_COL]

                if pd.isna(student_id):
                    continue

                student_id = str(student_id).strip()
                if not student_id:
                    continue

                if student_id not in students_dict:
                    students_dict[student_id] = {}

                for local_q, col_idx in col_map.items():
                    val = row.iloc[col_idx]
                    ans = str(val).strip().upper() if pd.notna(val) else ""

                    if ans not in ["A", "B", "C", "D"]:
                        ans = ""

                    q_id = local_q
                    students_dict[student_id][q_id] = ans

                    if q_id > max_q_id_found:
                        max_q_id_found = q_id

        if processed_sheets == 0:
            raise ValueError(f"No sheets matched target class '{target_class}' in Response_Online.xlsx")

        if not students_dict:
            raise ValueError("No valid student data found in online response")

        # =====================================
        # STEP 5: BUILD FINAL MATRIX
        # =====================================
        df_matrix = pd.DataFrame(students_dict)
        df_matrix = df_matrix.reindex(range(1, max_q_id_found + 1))
        df_matrix = df_matrix.fillna("")
        df_matrix.index.name = "question_id"

        logger.info("Online ResponseSheet matrix built successfully")

        return df_matrix, extracted_key
