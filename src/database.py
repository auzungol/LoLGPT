import sqlite3
import json
from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            champion TEXT NOT NULL,
            region TEXT NOT NULL DEFAULT 'Unknown',
            role TEXT NOT NULL DEFAULT 'Unknown',
            source_file TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_chunk(champion: str, source_file: str, content: str, embedding: list[float],
                  region: str = "Unknown", role: str = "Unknown"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chunks (champion, region, role, source_file, content, embedding) VALUES (?, ?, ?, ?, ?, ?)",
        (champion, region, role, source_file, content, json.dumps(embedding)),
    )
    conn.commit()
    conn.close()


def get_all_chunks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, champion, source_file, content, embedding FROM chunks")
    rows = cur.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]


def get_distinct_champions() -> list[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT champion FROM chunks")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_chunks_by_champion(champion: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, champion, source_file, content, embedding FROM chunks WHERE champion = ?",
        (champion,),
    )
    rows = cur.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]


def get_chunks_by_region(region: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, champion, source_file, content, embedding FROM chunks WHERE region = ?",
        (region,),
    )
    rows = cur.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]

def get_chunks_by_role(role: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, champion, source_file, content, embedding FROM chunks WHERE role LIKE ?",
        (f"%{role}%",),
    )
    rows = cur.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]
def clear_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM chunks")
    conn.commit()
    conn.close()