import sqlite3
from datetime import datetime

DB_NAME = "reception_log.db"

def init_db():
    """
    Creates the database table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT,
            raw_ocr_text TEXT, 
            tracking_code TEXT,
            recipient_name TEXT,
            sender_name TEXT,
            carrier TEXT,
            status TEXT DEFAULT 'RECEIVED',
            created_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized: {DB_NAME}")

def insert_package(image_path, raw_ocr_text, tracking_code, recipient_name, sender, carrier):
    """
    Inserts a new package record into the database.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO packages (image_path, raw_ocr_text, tracking_code, recipient_name, sender_name, carrier, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (image_path, raw_ocr_text, tracking_code, recipient_name, carrier, timestamp))
    conn.commit()
    conn.close()
    print(f"[DB] Package saved: {tracking_code} for {recipient_name}")