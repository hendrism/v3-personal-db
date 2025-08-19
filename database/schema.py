from .connection import get_db_connection


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

