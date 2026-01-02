from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple, Dict

class ResponseTransformer(ABC):
    """
    Base interface for response transformers.
    """

    @abstractmethod
    def transform(self, input_path: str, target_class: str) -> Tuple[pd.DataFrame, Dict[int, str]]:
        """
        Reads a raw response file and returns (StudentData, AnswerKey).
        
        Args:
           input_path: Path to the Excel file.
           target_class: The identifier for the class (e.g., '10FB') to filter or validate.

        Returns:
           Tuple[pd.DataFrame, Dict[int, str]]:
             - DataFrame with canonical columns
             - Dictionary mapping question_id (int) -> correct_option (str)
        
        The returned DataFrame MUST have exactly these columns:
        - student_id
        - question_id (int)
        - selected_option (str)
        - attempted (str: 'Y' or 'N')
        - marks_obtained (float/int)
        """
        pass
