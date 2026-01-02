import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def load_pdf_pages(file_path: str):
    """
    Generator that yields (page_number, page_text) from a PDF file.
    """
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            text = page.get_text()
            yield page_num + 1, text
        doc.close()
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        raise
