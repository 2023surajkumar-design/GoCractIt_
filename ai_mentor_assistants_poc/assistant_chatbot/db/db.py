import sqlite3

def init_db():
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(thread_id) REFERENCES threads(id)
        )
    """)
    conn.commit()
    conn.close()

def add_thread(thread_id):
    conn = sqlite3.connect("chat.db")
    conn.execute("INSERT OR IGNORE INTO threads (id) VALUES (?)", (thread_id,))
    conn.commit()
    conn.close()

def add_message(thread_id, role, content):
    conn = sqlite3.connect("chat.db")
    conn.execute(
        "INSERT INTO messages (thread_id, role, content) VALUES (?,?,?)",
        (thread_id, role, content)
    )
    conn.commit()
    conn.close()

def get_messages(thread_id):
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE thread_id=? ORDER BY created_at",
        (thread_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

init_db()