import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Drop existing table if it exists to recreate with new schema
cursor.execute('DROP TABLE IF EXISTS users')

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL
)
''')

# Insert sample users with hashed passwords and timestamps
current_time = datetime.now().isoformat()

cursor.execute(
    "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
    ('John Doe', 'john@example.com', hash_password('password123'), current_time)
)
cursor.execute(
    "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
    ('Jane Smith', 'jane@example.com', hash_password('secret456'), current_time)
)
cursor.execute(
    "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
    ('Bob Johnson', 'bob@example.com', hash_password('qwerty789'), current_time)
)

conn.commit()
conn.close()

print("Database initialized with sample data")
print("Sample users created with hashed passwords:")
print("- john@example.com / password123")
print("- jane@example.com / secret456") 
print("- bob@example.com / qwerty789")