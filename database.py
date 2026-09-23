import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "listings.db")

def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("CREATE TABLE IF NOT EXISTS listings (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, data TEXT NOT NULL)")
        db.commit()

def save_listing(data):
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("INSERT INTO listings(created_at, data) VALUES (?, ?)", (datetime.now(timezone.utc).isoformat(), json.dumps(data, ensure_ascii=False)))
        db.commit()
        return cur.lastrowid

def get_listing(listing_id):
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT id, created_at, data FROM listings WHERE id = ?", (listing_id,)).fetchone()
    if not row:
        return None
    return {"id": row[0], "created_at": row[1], **json.loads(row[2])}

def update_listing(listing_id, data):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("UPDATE listings SET data = ? WHERE id = ?", (json.dumps(data, ensure_ascii=False), listing_id))
        db.commit()
