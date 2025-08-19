# database.py - Enhanced with Objectives
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
    finally:
        conn.close()

def init_db():
    """Initialize database with all tables."""
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
        
        # NEW: Objectives table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS objectives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                target_percentage INTEGER DEFAULT 80,
                notes TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals (id)
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
        
        # Enhanced trial logs table - now links to objectives
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trial_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                objective_id INTEGER,
                goal_id INTEGER,
                independent INTEGER DEFAULT 0,
                minimal_support INTEGER DEFAULT 0,
                moderate_support INTEGER DEFAULT 0,
                maximal_support INTEGER DEFAULT 0,
                incorrect INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (objective_id) REFERENCES objectives (id),
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
        
        # Create indexes for better performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_goals_student ON goals(student_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_objectives_goal ON objectives(goal_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_student ON sessions(student_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trials_session ON trial_logs(session_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trials_objective ON trial_logs(objective_id)')
        
        conn.commit()

def add_sample_data():
    """Add some sample data for testing."""
    with get_db_connection() as conn:
        # Check if we already have data
        cursor = conn.execute('SELECT COUNT(*) FROM students')
        if cursor.fetchone()[0] > 0:
            print("Sample data already exists")
            return
        
        # Add sample student
        cursor = conn.execute('''
            INSERT INTO students (first_name, last_name, grade_level, pronouns)
            VALUES (?, ?, ?, ?)
        ''', ('Alex', 'Johnson', '3rd Grade', 'they/them'))
        student_id = cursor.lastrowid
        
        # Add sample goals
        cursor = conn.execute('''
            INSERT INTO goals (student_id, description, target_accuracy)
            VALUES (?, ?, ?)
        ''', (student_id, 'Improve articulation of /r/ sound in all positions', 85))
        goal1_id = cursor.lastrowid
        
        cursor = conn.execute('''
            INSERT INTO goals (student_id, description, target_accuracy)
            VALUES (?, ?, ?)
        ''', (student_id, 'Increase vocabulary comprehension and usage', 80))
        goal2_id = cursor.lastrowid
        
        # Add sample objectives for goal 1
        objectives_goal1 = [
            'Produce /r/ sound in initial position with 85% accuracy',
            'Produce /r/ sound in medial position with 85% accuracy',
            'Produce /r/ sound in final position with 85% accuracy',
            'Use /r/ words in connected speech with 80% accuracy'
        ]
        
        for obj_desc in objectives_goal1:
            conn.execute('''
                INSERT INTO objectives (goal_id, description, target_percentage)
                VALUES (?, ?, ?)
            ''', (goal1_id, obj_desc, 85))
        
        # Add sample objectives for goal 2
        objectives_goal2 = [
            'Define new vocabulary words with 80% accuracy',
            'Use new vocabulary in sentences with 75% accuracy',
            'Answer comprehension questions about vocabulary with 85% accuracy'
        ]
        
        for obj_desc in objectives_goal2:
            conn.execute('''
                INSERT INTO objectives (goal_id, description, target_percentage)
                VALUES (?, ?, ?)
            ''', (goal2_id, obj_desc, 80))
        
        conn.commit()
        print("Sample data added successfully!")

if __name__ == "__main__":
    init_db()
    add_sample_data()