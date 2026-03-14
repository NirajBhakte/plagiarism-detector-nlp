# src/preprocess.py

import nltk
import os
import re
from nltk.tokenize import sent_tokenize

# --- PDF Support ---
import pdfplumber


# -------------------------------------------------------- #
#  TEXT FILE UTILITIES
# -------------------------------------------------------- #

def load_text(file_path):
    """
    Reads plain text from a .txt file and returns it as a string.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    return text


# -------------------------------------------------------- #
#  PDF UTILITIES
# -------------------------------------------------------- #

def extract_text_from_pdf(file_path):
    """
    Extracts raw text from a PDF file using pdfplumber.

    pdfplumber is preferred over pypdf for academic/research PDFs
    because it correctly handles multi-column layouts, headers, and
    preserves paragraph spacing better.

    Args:
        file_path (str): Absolute path to the .pdf file.

    Returns:
        str: All extracted text joined from every page.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If no text could be extracted (e.g. scanned image PDF).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    all_text = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()

            if page_text:
                # Strip excessive whitespace within a page
                page_text = page_text.strip()
                all_text.append(page_text)
            else:
                # Could be a scanned image page — warn but continue
                print(f"  [Warning] Page {page_num} yielded no text. "
                      f"It may be a scanned/image page.")

    if not all_text:
        raise ValueError(
            f"No extractable text found in '{file_path}'. "
            "If it's a scanned PDF, OCR support is needed (pytesseract)."
        )

    # Join pages with a newline so sentence tokeniser sees page boundaries
    full_text = "\n".join(all_text)
    return full_text


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF given as raw bytes (used by the FastAPI upload endpoint).

    Args:
        file_bytes (bytes): Raw bytes of the uploaded PDF.

    Returns:
        str: Extracted text.
    """
    import io

    all_text = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()

            if page_text:
                all_text.append(page_text.strip())
            else:
                print(f"  [Warning] Page {page_num} yielded no text.")

    if not all_text:
        raise ValueError("No extractable text found in the uploaded PDF.")

    return "\n".join(all_text)


# -------------------------------------------------------- #
#  SHARED CLEANING + TOKENISATION
# -------------------------------------------------------- #

def clean_text(text):
    """
    Cleans text without breaking sentence boundaries.

    - Collapses whitespace runs into a single space
    - Removes non-ASCII / special chars while keeping sentence punctuation
    - Does NOT strip periods, commas, ? or ! so sent_tokenize works correctly
    """
    # Normalise all whitespace (tabs, newlines, multiple spaces) → single space
    text = re.sub(r"\s+", " ", text)

    # Keep only alphanumerics + basic punctuation needed for sentences
    text = re.sub(r"[^a-zA-Z0-9\s\.\,\?\!]", "", text)

    return text.strip()


def split_into_sentences(text):
    """
    Splits a cleaned text string into individual sentences using NLTK.

    Filters out very short fragments (< 10 chars) that aren't real sentences.
    """
    sentences = sent_tokenize(text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    return sentences


# -------------------------------------------------------- #
#  HIGH-LEVEL PIPELINE FUNCTIONS
# -------------------------------------------------------- #

def preprocess_text_file(file_path):
    """
    Full pipeline for a plain .txt file:
        load → clean → split into sentences
    """
    text = load_text(file_path)
    text = clean_text(text)
    sentences = split_into_sentences(text)
    return sentences


def preprocess_pdf_file(file_path):
    """
    Full pipeline for a .pdf file:
        extract → clean → split into sentences
    """
    text = extract_text_from_pdf(file_path)
    text = clean_text(text)
    sentences = split_into_sentences(text)
    return sentences


def preprocess_file(file_path):
    """
    Unified entry-point that auto-detects file type (.txt or .pdf)
    and runs the appropriate preprocessing pipeline.

    This is the function called by detector.py — no changes needed there.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return preprocess_pdf_file(file_path)
    elif ext == ".txt":
        return preprocess_text_file(file_path)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            "Only .txt and .pdf files are supported."
        )


def preprocess_raw_bytes(file_bytes: bytes, filename: str):
    """
    Used by the API upload endpoint.
    Detects whether uploaded bytes are a PDF or plain text and preprocesses.

    Args:
        file_bytes (bytes): Raw bytes from the uploaded file.
        filename   (str)  : Original filename (used for extension detection).

    Returns:
        list[str]: List of preprocessed sentences.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf_bytes(file_bytes)
    else:
        # Treat as plain text
        text = file_bytes.decode("utf-8", errors="replace")

    text = clean_text(text)
    return split_into_sentences(text)


# -------------------------------------------------------- #
#  QUICK TEST
# -------------------------------------------------------- #

if __name__ == "__main__":

    import sys

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Test with a .txt file
    txt_file = os.path.join(BASE_DIR, "data", "student_inputs", "input.txt")

    if os.path.exists(txt_file):
        print("=== TXT FILE TEST ===")
        sentences = preprocess_file(txt_file)
        print(f"Total sentences: {len(sentences)}")
        for i, s in enumerate(sentences[:5], 1):
            print(f"  {i}. {s}")

    # Test with a .pdf file if one is provided as CLI arg
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"\n=== PDF FILE TEST: {pdf_path} ===")
        sentences = preprocess_file(pdf_path)
        print(f"Total sentences: {len(sentences)}")
        for i, s in enumerate(sentences[:5], 1):
            print(f"  {i}. {s}")