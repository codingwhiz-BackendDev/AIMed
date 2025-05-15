import os
import re
import sys
from pathlib import Path
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def split_text(text, chunk_size=500, overlap=50):
    """
    Split text into overlapping chunks for better context preservation
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def create_chunks_by_section(text):
    """
    Split text by section headers to create more meaningful chunks
    """
    section_patterns = [
        r'\n\s*#+\s+(.+)',                          # Markdown-style headers
        r'\n\s*([A-Z][A-Za-z\s]{2,50}:)\s',         # Capitalized phrases with colon
        r'\n\s*([A-Z][A-Za-z\s]{2,40})\n',          # All-caps section titles
        r'\n\s*((?:Introduction|Symptoms|Treatment|Diagnosis|Prevention)[:\s])',  # Common medical section names
    ]
    combined_pattern = '|'.join(section_patterns)
    sections = re.split(combined_pattern, text)
    chunks = []
    for i in range(0, len(sections), 2):
        section_text = sections[i]
        if i + 1 < len(sections):
            header = sections[i + 1]
            section_text = f"{header}\n\n{section_text}"
        if len(section_text.split()) > 800:
            sub_chunks = split_text(section_text)
            chunks.extend(sub_chunks)
        else:
            chunks.append(section_text)
    return chunks

def save_chunks(chunks, output_dir='textbook_chunks'):
    """
    Save text chunks to separate files
    """
    os.makedirs(output_dir, exist_ok=True)
    for idx, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk:
            continue
        with open(os.path.join(output_dir, f"chunk_{idx:04d}.txt"), 'w', encoding='utf-8') as f:
            f.write(chunk)

def main():
    input_file = 'static/The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf'
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return
    
    print(f"Processing '{input_file}'...")

    try:
        full_text = extract_text_from_pdf(input_file)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return

    chunks = create_chunks_by_section(full_text)
    if len(chunks) < 5:
        print("Few section headers found, using regular text splitting...")
        chunks = split_text(full_text)

    save_chunks(chunks)
    print(f"Successfully processed medical textbook into {len(chunks)} chunks!")
    print(f"Chunks saved to 'textbook_chunks/' directory")

if __name__ == "__main__":
    main()
