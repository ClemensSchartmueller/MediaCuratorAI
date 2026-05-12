import sqlite3
from src.config import Config

class Database:
    def __init__(self, db_path=Config.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for taste profile
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS taste_profile (
                    id INTEGER PRIMARY KEY,
                    profile_text TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for weekly recommendations mapping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tmdb_id INTEGER,
                    title TEXT,
                    media_type TEXT, -- 'movie' or 'tv'
                    position INTEGER, -- 1, 2, 3...
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table for tracking processed items to avoid duplicates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_items (
                    tmdb_id INTEGER PRIMARY KEY,
                    media_type TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_taste_profile(self, profile_text):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO taste_profile (id, profile_text, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)", (profile_text,))
            conn.commit()

    def get_taste_profile(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT profile_text FROM taste_profile WHERE id = 1")
            row = cursor.fetchone()
            return row[0] if row else None

    def set_active_recommendations(self, recommendations):
        # recommendations is a list of dicts: {'tmdb_id': 123, 'title': '...', 'media_type': 'movie', 'position': 1}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_recommendations")
            for rec in recommendations:
                cursor.execute("""
                    INSERT INTO active_recommendations (tmdb_id, title, media_type, position)
                    VALUES (?, ?, ?, ?)
                """, (rec['tmdb_id'], rec['title'], rec['media_type'], rec['position']))
            conn.commit()

    def get_recommendation_by_position(self, position):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tmdb_id, title, media_type FROM active_recommendations WHERE position = ?", (position,))
            return cursor.fetchone()

    def get_recommendation_by_title_fragment(self, fragment):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tmdb_id, title, media_type FROM active_recommendations WHERE title LIKE ?", (f"%{fragment}%",))
            return cursor.fetchone()
