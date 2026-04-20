FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    && apt-get clean

WORKDIR /app

COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    pymupdf \
    pytesseract \
    opencv-python \
    pandas \
    openpyxl \
    xlrd \
    pyxlsb \
    python-pptx \
    python-docx \
    beautifulsoup4 \
    together \
    faiss-cpu \
    python-dotenv

CMD ["python", "main.py"]