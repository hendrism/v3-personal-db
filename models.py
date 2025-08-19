from datetime import datetime, date, timedelta
import sqlite3
import inspect

class BaseModel:
    """Base model with common functionality."""
    
    @classmethod
    def get_by_id(cls, db, id):
        cursor = db.execute(f"SELECT * FROM {cls.table_name} WHERE id = ?", (id,))
        row = cursor.fetchone()
        return cls.from_row(row) if row else None
    
    @classmethod
    def from_row(cls, row):
        """Create instance from database row.
        Filters out unexpected keys so JOINed columns don't break constructors.
        Also attaches any extra columns to the instance as attributes.
        """
        if not row:
            return None
        data = dict(row)
        allowed = cls._allowed_fields()
        filtered = {k: v for k, v in data.items() if k in allowed}
        inst = cls(**filtered)
        # Attach any extra columns so callers can still access them if needed
        for k, v in data.items():
            if k not in allowed:
                setattr(inst, k, v)
        return inst

    @classmethod
    def _allowed_fields(cls):
        """Return constructor argument names (excluding 'self')."""
        sig = inspect.signature(cls.__init__)
        # Keep parameters that can be passed as kwargs
        names = [p.name for p in sig.parameters.values() if p.name != 'self']
        return set(names)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_')}

class Student(BaseModel):
    table_name = 'students'
    
    def __init__(self, id=None, first_name='', last_name='', preferred_name='', 
                 pronouns='', grade_level='', notes='', active=True, 
                 created_at=None, updated_at=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.preferred_name = preferred_name
        self.pronouns = pronouns
        self.grade_level = grade_level
        self.notes = notes
        self.active = active
        self.created_at = created_at
        self.updated_at = updated_at
    
    @property
    def display_name(self):
        """Name to display in UI."""
        if self.preferred_name:
            return f"{self.preferred_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @classmethod
    def get_all(cls, db):
        cursor = db.execute("SELECT * FROM students WHERE active = 1 ORDER BY last_name, first_name")
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_active(cls, db):
        return cls.get_all(db)
    
    @classmethod
    def create(cls, db, data):
        cursor = db.execute('''
            INSERT INTO students (first_name, last_name, preferred_name, pronouns, grade_level, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['first_name'], data['last_name'], data.get('preferred_name'), 
              data.get('pronouns'), data.get('grade_level'), data.get('notes')))
        
        student_id = cursor.lastrowid
        db.commit()
        return cls.get_by_id(db, student_id)

class Goal(BaseModel):
    table_name = 'goals'
    
    def __init__(self, id=None, student_id=None, description='', target_accuracy=80, 
                 active=True, created_at=None):
        self.id = id
        self.student_id = student_id
        self.description = description
        self.target_accuracy = target_accuracy
        self.active = active
        self.created_at = created_at
    
    @classmethod
    def get_by_student(cls, db, student_id):
        cursor = db.execute("SELECT * FROM goals WHERE student_id = ? AND active = 1", (student_id,))
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def create(cls, db, data):
        cursor = db.execute('''
            INSERT INTO goals (student_id, description, target_accuracy)
            VALUES (?, ?, ?)
        ''', (data['student_id'], data['description'], data.get('target_accuracy', 80)))
        
        goal_id = cursor.lastrowid
        db.commit()
        return cls.get_by_id(db, goal_id)

class Session(BaseModel):
    table_name = 'sessions'
    
    def __init__(self, id=None, student_id=None, session_date=None, start_time=None, 
                 end_time=None, session_type='Individual', location='', status='Completed', 
                 notes='', created_at=None):
        self.id = id
        self.student_id = student_id
        self.session_date = session_date
        self.start_time = start_time
        self.end_time = end_time
        self.session_type = session_type
        self.location = location
        self.status = status
        self.notes = notes
        self.created_at = created_at
    
    def this_week(self):
        """Check if session is this week."""
        if not self.session_date:
            return False
        session_date = datetime.strptime(self.session_date, '%Y-%m-%d').date()
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start <= session_date <= week_end
    
    @classmethod
    def get_recent(cls, db, limit=10):
        cursor = db.execute('''
            SELECT s.*, st.first_name, st.last_name 
            FROM sessions s 
            JOIN students st ON s.student_id = st.id 
            ORDER BY s.session_date DESC, s.created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            session = cls.from_row(row)
            session.student_name = f"{row['first_name']} {row['last_name']}"
            sessions.append(session)
        return sessions
    
    @classmethod
    def get_recent_with_student_info(cls, db, limit=20):
        """Get recent sessions with student names and SOAP note status."""
        cursor = db.execute('''
            SELECT s.*, st.first_name, st.last_name,
                   CASE WHEN sn.id IS NOT NULL THEN 1 ELSE 0 END as has_soap_note
            FROM sessions s 
            JOIN students st ON s.student_id = st.id 
            LEFT JOIN soap_notes sn ON s.id = sn.session_id
            ORDER BY s.session_date DESC, s.created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            session = cls.from_row(row)
            session.student_name = f"{row['first_name']} {row['last_name']}"
            session.has_soap_note = bool(row['has_soap_note'])
            sessions.append(session)
        return sessions
    
    @classmethod
    def get_by_date_with_student_info(cls, db, date_str):
        """Get sessions by date with student names and SOAP note status."""
        cursor = db.execute('''
            SELECT s.*, st.first_name, st.last_name,
                   CASE WHEN sn.id IS NOT NULL THEN 1 ELSE 0 END as has_soap_note
            FROM sessions s 
            JOIN students st ON s.student_id = st.id 
            LEFT JOIN soap_notes sn ON s.id = sn.session_id
            WHERE s.session_date = ?
            ORDER BY s.start_time, s.created_at
        ''', (date_str,))
        
        sessions = []
        for row in cursor.fetchall():
            session = cls.from_row(row)
            session.student_name = f"{row['first_name']} {row['last_name']}"
            session.has_soap_note = bool(row['has_soap_note'])
            sessions.append(session)
        return sessions
    
    @classmethod
    def get_by_student(cls, db, student_id):
        cursor = db.execute("SELECT * FROM sessions WHERE student_id = ? ORDER BY session_date DESC", (student_id,))
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_by_date(cls, db, date_str):
        cursor = db.execute('''
            SELECT s.*, st.first_name, st.last_name 
            FROM sessions s 
            JOIN students st ON s.student_id = st.id 
            WHERE s.session_date = ?
            ORDER BY s.start_time, s.created_at
        ''', (date_str,))
        
        sessions = []
        for row in cursor.fetchall():
            session = cls.from_row(row)
            session.student_name = f"{row['first_name']} {row['last_name']}"
            sessions.append(session)
        return sessions
    
    @classmethod
    def get_upcoming(cls, db, days=7):
        end_date = (date.today() + timedelta(days=days)).isoformat()
        cursor = db.execute("SELECT * FROM sessions WHERE session_date >= date('now') AND session_date <= ?", (end_date,))
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_pending_soap_notes(cls, db):
        cursor = db.execute('''
            SELECT s.* FROM sessions s 
            LEFT JOIN soap_notes sn ON s.id = sn.session_id 
            WHERE sn.id IS NULL AND s.status = 'Completed'
            ORDER BY s.session_date DESC
        ''')
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def create(cls, db, data):
        cursor = db.execute('''
            INSERT INTO sessions (student_id, session_date, start_time, end_time, 
                                session_type, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['student_id'], data['session_date'], data.get('start_time'),
              data.get('end_time'), data.get('session_type', 'Individual'),
              data.get('location'), data.get('notes')))
        
        session_id = cursor.lastrowid
        db.commit()
        return cls.get_by_id(db, session_id)

class TrialLog(BaseModel):
    table_name = 'trial_logs'
    
    def __init__(self, id=None, session_id=None, goal_id=None, independent=0, 
                 minimal_support=0, moderate_support=0, maximal_support=0, 
                 incorrect=0, notes='', created_at=None):
        self.id = id
        self.session_id = session_id
        self.goal_id = goal_id
        self.independent = independent or 0
        self.minimal_support = minimal_support or 0
        self.moderate_support = moderate_support or 0
        self.maximal_support = maximal_support or 0
        self.incorrect = incorrect or 0
        self.notes = notes
        self.created_at = created_at
    
    @property
    def total_trials(self):
        return (self.independent + self.minimal_support + 
                self.moderate_support + self.maximal_support + self.incorrect)
    
    @property
    def independence_percentage(self):
        total = self.total_trials
        return round((self.independent / total) * 100, 1) if total > 0 else 0
    
    @property
    def success_percentage(self):
        total = self.total_trials
        successful = (self.independent + self.minimal_support + 
                     self.moderate_support + self.maximal_support)
        return round((successful / total) * 100, 1) if total > 0 else 0
    
    @classmethod
    def get_by_session(cls, db, session_id):
        cursor = db.execute("SELECT * FROM trial_logs WHERE session_id = ?", (session_id,))
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_recent_by_student(cls, db, student_id, limit=10):
        cursor = db.execute('''
            SELECT tl.* FROM trial_logs tl 
            JOIN sessions s ON tl.session_id = s.id 
            WHERE s.student_id = ? 
            ORDER BY s.session_date DESC, tl.created_at DESC 
            LIMIT ?
        ''', (student_id, limit))
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def create(cls, db, data):
        cursor = db.execute('''
            INSERT INTO trial_logs (session_id, goal_id, independent, minimal_support, 
                                  moderate_support, maximal_support, incorrect, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['session_id'], data.get('goal_id'), data['independent'],
              data['minimal_support'], data['moderate_support'], 
              data['maximal_support'], data['incorrect'], data.get('notes')))
        
        trial_id = cursor.lastrowid
        db.commit()
        return cls.get_by_id(db, trial_id)

class SOAPNote(BaseModel):
    table_name = 'soap_notes'
    
    def __init__(self, id=None, session_id=None, subjective='', objective='', 
                 assessment='', plan='', created_at=None, updated_at=None):
        self.id = id
        self.session_id = session_id
        self.subjective = subjective
        self.objective = objective
        self.assessment = assessment
        self.plan = plan
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def get_by_session(cls, db, session_id):
        cursor = db.execute("SELECT * FROM soap_notes WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        return cls.from_row(row) if row else None
    
    @classmethod
    def get_by_student(cls, db, student_id):
        cursor = db.execute('''
            SELECT sn.* FROM soap_notes sn 
            JOIN sessions s ON sn.session_id = s.id 
            WHERE s.student_id = ? 
            ORDER BY s.session_date DESC
        ''', (student_id,))
        return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def generate_from_session(cls, db, session):
        """Auto-generate basic SOAP note from session data."""
        # Get trial data for this session
        trials = TrialLog.get_by_session(db, session.id)
        
        # Generate basic content
        subjective = f"Student participated in {session.session_type.lower()} therapy session."
        
        objective = "Trial data collected:\n"
        for trial in trials:
            objective += f"- {trial.total_trials} trials, {trial.independence_percentage}% independence\n"
        
        assessment = f"Student demonstrated varying levels of support needs across targeted skills."
        
        plan = "Continue current intervention approach with focus on increasing independence."
        
        return cls(
            session_id=session.id,
            subjective=subjective,
            objective=objective,
            assessment=assessment,
            plan=plan
        )
    
    @classmethod
    def create_or_update(cls, db, data):
        existing = cls.get_by_session(db, data['session_id'])
        
        if existing:
            # Update existing
            db.execute('''
                UPDATE soap_notes 
                SET subjective = ?, objective = ?, assessment = ?, plan = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (data['subjective'], data['objective'], data['assessment'], 
                  data['plan'], data['session_id']))
            db.commit()
            return cls.get_by_session(db, data['session_id'])
        else:
            # Create new
            cursor = db.execute('''
                INSERT INTO soap_notes (session_id, subjective, objective, assessment, plan)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['session_id'], data['subjective'], data['objective'], 
                  data['assessment'], data['plan']))
            
            soap_id = cursor.lastrowid
            db.commit()
            return cls.get_by_id(db, soap_id)