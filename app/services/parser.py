import logging
import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path):
    """Extract all text from a PDF file, with page separators and error handling."""
    try:
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                else:
                    logger.warning(f"Page {i + 1} returned no text (may be an image/scan).")

        if not text_parts:
            logger.error(f"No text extracted from PDF: {file_path}")
            return "No readable text found in the uploaded PDF."

        return "\n\n".join(text_parts)

    except Exception as e:
        logger.error(f"Failed to parse PDF '{file_path}': {e}")
        return f"Error reading PDF: {str(e)}"