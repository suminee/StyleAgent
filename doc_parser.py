"""Document parser for extracting text from various file formats"""
from pathlib import Path
from typing import List
from docx import Document


def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from a .docx file"""
    doc = Document(file_path)
    paragraphs = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def extract_text_from_txt(file_path: str) -> str:
    """Extract text content from a .txt file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_sample_documents(directory: str) -> List[dict]:
    """Load all documents from a directory"""
    samples = []
    dir_path = Path(directory)

    for file_path in dir_path.iterdir():
        if file_path.suffix.lower() == ".docx":
            text = extract_text_from_docx(str(file_path))
            samples.append({
                "filename": file_path.name,
                "content": text,
                "type": "docx"
            })
        elif file_path.suffix.lower() == ".txt":
            text = extract_text_from_txt(str(file_path))
            samples.append({
                "filename": file_path.name,
                "content": text,
                "type": "txt"
            })

    return samples


if __name__ == "__main__":
    # Test
    from config import SAMPLES_DIR
    docs = load_sample_documents(SAMPLES_DIR)
    print(f"Loaded {len(docs)} documents")
    for doc in docs:
        print(f"  - {doc['filename']}: {len(doc['content'])} chars")
