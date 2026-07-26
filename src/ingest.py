import os
import re
from config import CHAMPION_FOLDER
from database import init_db, insert_chunk, clear_db
from embedding import embed_text
from lanes import get_lanes_for_champion


def chunk_text(text: str, max_chars: int = 500) -> list[str]:
    """Split text into paragraph-based chunks, merging short ones up to max_chars."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def load_champion_files() -> list[tuple[str, str]]:
    """Returns list of (champion_name, file_content)."""
    files = []
    for filename in os.listdir(CHAMPION_FOLDER):
        if filename.endswith(".txt"):
            champion_name = os.path.splitext(filename)[0]
            path = os.path.join(CHAMPION_FOLDER, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            files.append((champion_name, content))
    return files


def extract_region(content: str) -> str:
    match = re.search(r"^Region:\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Unknown"


def extract_role(content: str) -> str:
    match = re.search(r"^Role:\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Unknown"


def extract_resource(content: str) -> str:
    match = re.search(r"^Resource:\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Unknown"


def run_ingestion(reset: bool = True):
    print("A: run_ingestion başladı", flush=True)
    try:
        if reset:
            init_db()
            print("B: init_db tamam", flush=True)
            clear_db()
            print("C: clear_db tamam", flush=True)
        else:
            init_db()

        champions = load_champion_files()
        print("D: dosyalar okundu, sayi =", len(champions), flush=True)

        for champion_name, content in champions:
            region = extract_region(content)
            role = extract_role(content)
            resource = extract_resource(content)
            lane = ", ".join(get_lanes_for_champion(champion_name))
            print("E:", champion_name, "işleniyor", flush=True)
            chunks = chunk_text(content)
            print("F:", champion_name, "chunk sayisi =", len(chunks), flush=True)
            if not chunks:
                continue

            embeddings = [embed_text(chunk) for chunk in chunks]
            print("G:", champion_name, "embed tamam", flush=True)

            for chunk, embedding in zip(chunks, embeddings):
                insert_chunk(
                    champion=champion_name,
                    source_file=f"{champion_name}.txt",
                    content=chunk,
                    embedding=embedding,
                    region=region,
                    role=role,
                    lane=lane,
                    resource=resource,
                )
            print("H:", champion_name, "DB'ye yazildi", flush=True)

        print("I: ingestion tamamlandi", flush=True)
    except Exception as e:
        import traceback
        print("HATA:", e, flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    run_ingestion()