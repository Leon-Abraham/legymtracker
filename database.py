import sqlite3
import os

DATABASE_FILE = os.path.join(os.path.dirname(__file__), "gym.db")

def get_connection():
    """Return a new SQLite database connection."""
    return sqlite3.connect(DATABASE_FILE)

def init_db():
    """Create users and workouts tables if they do not exist."""
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Create the users table if it doesn't exist
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            last_payment_date TEXT,  -- New column for payment date
            expiry_date TEXT  -- New column for expiry date
        )
        """)

        # Create the workouts table if it doesn't exist
        cur.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            date TEXT NOT NULL
        )
        """)

        conn.commit()
    finally:
        conn.close()

def get_user_by_username(username):
    """Return (id, username, password, email, last_payment_date, expiry_date) or None."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password, email, last_payment_date, expiry_date FROM users WHERE username = ?",
            (username,)
        )
        return cur.fetchone()
    finally:
        conn.close()

def create_user(username, password_hash, email="", last_payment_date=None, expiry_date=None):
    """Insert a user; returns id or None on duplicate."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, email, last_payment_date, expiry_date) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, email, last_payment_date, expiry_date),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()

def update_payment(user_id, payment_date, expiry_date):
    """Update the payment details for the user."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET last_payment_date = ?, expiry_date = ?
            WHERE id = ?
        """, (payment_date, expiry_date, user_id))
        conn.commit()
    finally:
        conn.close()

def add_payment_columns():
    """Ensure that the columns for payment info (last_payment_date, expiry_date) exist in the users table."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Check if the columns already exist
        cur.execute("""
            PRAGMA table_info(users);
        """)
        
        columns = [column[1] for column in cur.fetchall()]
        
        if 'last_payment_date' not in columns:
            cur.execute("""
                ALTER TABLE users ADD COLUMN last_payment_date TEXT;
            """)
        
        if 'expiry_date' not in columns:
            cur.execute("""
                ALTER TABLE users ADD COLUMN expiry_date TEXT;
            """)
        
        conn.commit()
    finally:
        conn.close()


def get_workouts_by_user(user_id):
    """Get all workouts for a user."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, date FROM workouts WHERE user_id = ? ORDER BY date",
            (user_id,)
        )
        return cur.fetchall()
    finally:
        conn.close()

def workout_exists_on_date(user_id, date_str):
    """Check if a workout already exists for a given date."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM workouts WHERE user_id = ? AND date LIKE ? LIMIT 1",
            (user_id, date_str + "%"),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()
