import sqlite3

from constants import DATABASE

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Step 1: Create a new table with the new column
cursor.execute("DROP TABLE new_conversations")
cursor.execute("""
    CREATE TABLE new_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        summary TEXT NOT NULL,
        model TEXT NOT NULL
    )
""")

# Step 2: Copy data from the old table to the new table
cursor.execute("""
    INSERT INTO new_conversations (id, content, created_at, summary, model)
    SELECT id, content, created_at, summary, 'typhoon-v2-70b-instruct' FROM conversations
""")

# Step 4: Drop the old table
cursor.execute("DROP TABLE conversations")

# Step 5: Rename the new table to the old table's name
cursor.execute("ALTER TABLE new_conversations RENAME TO conversations")

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Migration completed successfully.")
