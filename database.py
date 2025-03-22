import sqlite3
import json
from config import config

class DatabaseManager:
    def __init__(self, db_name=None):
        if db_name is None:
             self.db_name = config["database"]["name"]
        else:
            self.db_name = db_name
        self.conn = None

    def connect(self):
        """Establishes a connection to the database."""
        self.conn = sqlite3.connect(self.db_name)

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_db(self):
        """Initializes the database table."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                user_id INTEGER PRIMARY KEY,
                chat_id TEXT,
                conversation_history TEXT
            )
        """)
        self.conn.commit()
        self.close()

    async def save_chat_session(self, user_id, chat_id, conversation_history):
        """Saves a chat session to the database using JSON serialization."""
        self.connect()
        cursor = self.conn.cursor()
        history_json = json.dumps(conversation_history)  # Serialize to JSON
        cursor.execute("""
            INSERT OR REPLACE INTO chat_sessions (user_id, chat_id, conversation_history)
            VALUES (?, ?, ?)
        """, (user_id, chat_id, history_json))
        self.conn.commit()
        self.close()

    async def get_chat_session(self, user_id):
        """Retrieves a chat session from the database, deserializing from JSON."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT chat_id, conversation_history FROM chat_sessions WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        self.close()

        if result:
            chat_id, history_json = result
            conversation_history = json.loads(history_json)  # Deserialize from JSON
            return chat_id, conversation_history
        else:
            return None, []
