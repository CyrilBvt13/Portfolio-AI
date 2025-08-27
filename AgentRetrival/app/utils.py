import os, json
from typing import List, Dict
import fitz # PyMuPDF
import pandas as pd
from docx import Document

def read_pdf(path: str) -> str:
    """Extract text content from a PDF file using PyMuPDF.

    Args:
        path (str): Path to the PDF file.

    Returns:
        str: Concatenated text from all pages of the PDF.
    """
    doc = fitz.open(path)
    parts = []
    for p in doc:
        parts.append(p.get_text())
    return "\n".join(parts)

def read_csv(path: str, max_rows: int = 50000) -> str:
    """Read a CSV file and convert it into a string representation.

    Args:
        path (str): Path to the CSV file.
        max_rows (int, optional): Maximum number of rows to load. Defaults to 50k.

    Returns:
        str: String representation of the dataframe in CSV format.
    """
    df = pd.read_csv(path, nrows=max_rows)
    return df.to_csv(index=False)

def read_docx(path: str) -> str:
    """Extract text content from a DOCX file.

    Args:
        path (str): Path to the DOCX file.

    Returns:
        str: Concatenated text of all non-empty paragraphs.
    """
    d = Document(path)
    return "\n".join(p.text for p in d.paragraphs if p.text.strip())

def recursive_split(text: str, chunk_size=1200, overlap=200) -> List[str]:
    """Split text into overlapping chunks.

    Args:
        text (str): Input text.
        chunk_size (int, optional): Maximum length of each chunk. Defaults to 1200.
        overlap (int, optional): Overlap size between chunks. Defaults to 200.

    Returns:
        List[str]: List of text chunks.
    """
    chunks, start = [], 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            start = end - overlap
        if start < 0:
            start = 0
    return chunks

def load_any(path: str) -> str:
    """Load text content from a file (PDF, CSV, or DOCX).

    Args:
        path (str): Path to the file.

    Returns:
        str: Extracted text.

    Raises:
        ValueError: If file extension is not supported.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        return read_pdf(path)
    if ext == '.csv':
        return read_csv(path)
    if ext in ('.docx',):
        return read_docx(path)
    raise ValueError(f"Extension non supportée: {ext}")