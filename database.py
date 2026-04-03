import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DATABASE_PATH", "annobot.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            message TEXT NOT NULL,
            schedule_type TEXT NOT NULL CHECK(schedule_type IN ('weekly', 'cron')),
            schedule_value TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            last_message_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def get_announcements(enabled_only=False):
    conn = get_connection()
    query = "SELECT * FROM announcements"
    if enabled_only:
        query += " WHERE enabled = 1"
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_announcement(announcement_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM announcements WHERE id = ?", (announcement_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_announcement(channel_id, message, schedule_type, schedule_value):
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO announcements (channel_id, message, schedule_type, schedule_value)
           VALUES (?, ?, ?, ?)""",
        (str(channel_id), message, schedule_type, schedule_value),
    )
    conn.commit()
    announcement_id = cursor.lastrowid
    conn.close()
    return announcement_id


def update_announcement(announcement_id, channel_id, message, schedule_type, schedule_value):
    conn = get_connection()
    conn.execute(
        """UPDATE announcements
           SET channel_id = ?, message = ?, schedule_type = ?,
               schedule_value = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (str(channel_id), message, schedule_type, schedule_value, announcement_id),
    )
    conn.commit()
    conn.close()


def delete_announcement(announcement_id):
    conn = get_connection()
    conn.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    conn.commit()
    conn.close()


def toggle_announcement(announcement_id):
    conn = get_connection()
    conn.execute(
        """UPDATE announcements
           SET enabled = NOT enabled, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (announcement_id,),
    )
    conn.commit()
    conn.close()


def set_last_message_id(announcement_id, message_id):
    conn = get_connection()
    conn.execute(
        "UPDATE announcements SET last_message_id = ? WHERE id = ?",
        (message_id, announcement_id),
    )
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        """INSERT INTO settings (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value = ?""",
        (key, value, value),
    )
    conn.commit()
    conn.close()
