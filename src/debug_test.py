import sys
print("1: script başladı", flush=True)

from config import CHAMPION_FOLDER
print("2: config import edildi, CHAMPION_FOLDER =", CHAMPION_FOLDER, flush=True)

from database import init_db, insert_chunk, clear_db
print("3: database import edildi", flush=True)

from embedding import embed_batch
print("4: embedding import edildi", flush=True)

init_db()
print("5: init_db çalıştı", flush=True)

from ingest import load_champion_files
print("6: ingest import edildi", flush=True)

files = load_champion_files()
print("7: dosyalar okundu, sayı =", len(files), flush=True)

print("8: embed_batch çağrılıyor...", flush=True)
vecs = embed_batch(["test cümlesi"])
print("9: embed_batch tamamlandı, uzunluk =", len(vecs[0]), flush=True)