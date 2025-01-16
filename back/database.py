import json
import psycopg2
from datetime import datetime

class DatabaseCheckpointer:
    def __init__(self, db_config):
        self.connection = psycopg2.connect(**db_config)
        self.cursor = self.connection.cursor()

    def save_state(self, thread_id, state):
        """Save or update the state in the database."""
        state_json = json.dumps(state)
        timestamp = datetime.utcnow()
        query = """
        INSERT INTO conversation_state (thread_id, state_data, last_updated)
        VALUES (%s, %s, %s)
        ON CONFLICT (thread_id)
        DO UPDATE SET state_data = EXCLUDED.state_data, last_updated = EXCLUDED.last_updated;
        """
        self.cursor.execute(query, (thread_id, state_json, timestamp))
        self.connection.commit()

    def load_state(self, thread_id):
        """Load the state from the database."""
        query = "SELECT state_data FROM conversation_state WHERE thread_id = %s;"
        self.cursor.execute(query, (thread_id,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])  # Deserialize JSON state
        return None  # No state found for this thread

    def close(self):
        """Close the database connection."""
        self.cursor.close()
        self.connection.close()
