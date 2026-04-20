import fitz
def detect_file_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return ext

def is_pdf_readable(file_path):
    doc = fitz.open(file_path)
    for page in doc:
        if page.get_text().strip():
            return True
    return False

def extract_pdf_text(file):
    doc = fitz.open(file)
    return " ".join([p.get_text() for p in doc])

def extract_pdf_ocr(file):
    from pdf2image import convert_from_path
    images = convert_from_path(file)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

import os
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
import pandas as pd

def dataframe_to_text(df):
    rows = []
    cols = df.columns.tolist()

    for _, row in df.iterrows():
        row_text = ", ".join([f"{col}: {row[col]}" for col in cols])
        rows.append(row_text)

    return "\n".join(rows)

def extract_excel(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".xlsx":
            df = pd.read_excel(file_path, engine="openpyxl")

        elif ext == ".xls":
            df = pd.read_excel(file_path, engine="xlrd")

        elif ext == ".xlsb":
            df = pd.read_excel(file_path, engine="pyxlsb")

        else:
            return ""

        return dataframe_to_text(df)

    except Exception as e:
        print(f"Excel read error ({file_path}): {e}")
        return ""
def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    try:
        # ---------- PDF ----------
        if ext == ".pdf":
            return extract_pdf_text(file_path) if is_pdf_readable(file_path) else extract_pdf_ocr(file_path)

        # ---------- IMAGE ----------
        elif ext in [".png", ".jpg", ".jpeg"]:
            return pytesseract.image_to_string(Image.open(file_path))

        # ---------- HTML ----------
        elif ext in [".html", ".htm"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f, "html.parser").get_text()

        # ---------- EXCEL ----------
        elif ext in [".xlsx", ".xls", ".xlsb"]:
            return extract_excel(file_path)

        # ---------- TEXT ----------
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        else:
            print(f"Unsupported file: {file_path}")
            return ""

    except Exception as e:
        print(f"Error extracting {file_path}: {e}")
        return ""