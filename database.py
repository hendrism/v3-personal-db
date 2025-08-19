import sqlite3
import os
from contextlib import contextmanager

DATABASE_PATH = os.path.join('data', 'students.db')

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with tables."""
    with get_db_connection() as conn:
        # Students table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                preferred_name TEXT,
                pronouns TEXT,
                grade_level TEXT,
                notes TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Goals table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                target_accuracy INTEGER DEFAULT 80,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        # Sessions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                session_date DATE NOT NULL,
                start_time TIME,
                end_time TIME,
                session_type TEXT DEFAULT 'Individual',
                location TEXT,
                status TEXT DEFAULT 'Completed',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        # Trial logs table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trial_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                goal_id INTEGER,
                independent INTEGER DEFAULT 0,
                minimal_support INTEGER DEFAULT 0,
                moderate_support INTEGER DEFAULT 0,
                maximal_support INTEGER DEFAULT 0,
                incorrect INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (goal_id) REFERENCES goals (id)
            )
        ''')
        
        # SOAP notes table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS soap_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                subjective TEXT,
                objective TEXT,
                assessment TEXT,
                plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

         # Schools table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS schools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                fax TEXT,
                hours TEXT,
                schedule_type TEXT DEFAULT 'simple',
                current_extension TEXT DEFAULT 'regular',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Student schedules table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS student_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                lunch_type TEXT DEFAULT 'A',
                classes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (school_id) REFERENCES schools (id)
            )
        ''')
        
        # Create default Thomas Stone High School if it doesn't exist
        cursor = conn.execute("SELECT COUNT(*) FROM schools WHERE name = 'Thomas Stone High School'")
        if cursor.fetchone()[0] == 0:
            conn.execute('''
                INSERT INTO schools (name, address, phone, fax, hours, schedule_type, current_extension)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                "Thomas Stone High School",
                "3785 Leonardtown Road, Waldorf, MD 20601",
                "(301) 934-4410",
                "(301) 932-6610",
                "7:15 AM - 2:15 PM",
                "thomas_stone",
                "regular"
            ))