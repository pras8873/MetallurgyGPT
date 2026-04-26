from backend.ingestion.pipeline import process_folder
from backend.vector_store.faiss_store import init_faiss, save_faiss
import pytesseract
print(pytesseract.image_to_string("test.png"))
if __name__ == "__main__":
    index, metadata = init_faiss()
    process_folder(r"F:\from official laptop\R&D\papers\LITERATURE", index, metadata)
    save_faiss(index, metadata)
    print("Ingestion complete!")
