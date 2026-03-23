# NeuroGuard Clinic – Database Module (Stub)
# TODO: Implement MySQL connection + session storage

import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Database:
    """MySQL database operations for NeuroGuard."""

    def __init__(self):
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'ej'),
            'password': os.getenv('MYSQL_PASSWORD', 'ej'),
            'database': os.getenv('MYSQL_DB', 'neuroguard')
        }
        self.init_db()

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def init_db(self):
        """Initialize database tables if they do not exist."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully.")
        except mysql.connector.Error as err:
            print(f"Error initializing database: {err}")

    def save_session(self, session_data):
        """Save a test session to the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO sessions (session_data) VALUES (%s)', (str(session_data),))
            conn.commit()
            session_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return session_id
        except mysql.connector.Error as err:
            print(f"Error saving session: {err}")
            return None

    def get_session(self, session_id):
        """Retrieve a session by ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM sessions WHERE id = %s', (session_id,))
            session = cursor.fetchone()
            cursor.close()
            conn.close()
            return session
        except mysql.connector.Error as err:
            print(f"Error getting session: {err}")
            return None

    def get_all_sessions(self):
        """Retrieve all past sessions."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM sessions ORDER BY created_at DESC')
            sessions = cursor.fetchall()
            cursor.close()
            conn.close()
            return sessions
        except mysql.connector.Error as err:
            print(f"Error getting sessions: {err}")
            return []

    def delete_session(self, session_id):
        """Delete a session."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE id = %s', (session_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except mysql.connector.Error as err:
            print(f"Error deleting session: {err}")
            return False
