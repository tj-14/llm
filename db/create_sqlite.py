import sqlite3

from ..constants import DATABASE

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create the conversations table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        summary TEXT NOT NULL,
        model TEXT NOT NULL
    )
""")

# Commit the changes
conn.commit()
