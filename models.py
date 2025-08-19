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
        
class School:
    def __init__(self, id=None, name=None, address=None, phone=None, fax=None, 
                 hours=None, schedule_type='simple', current_extension='regular', 
                 created_at=None):
        self.id = id
        self.name = name
        self.address = address
        self.phone = phone
        self.fax = fax
        self.hours = hours
        self.schedule_type = schedule_type  # 'simple' or 'thomas_stone'
        self.current_extension = current_extension
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def create_table(cls, db):
        """Create the schools table."""
        db.execute('''
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
        db.commit()
    
    @classmethod
    def get_all(cls, db):
        """Get all schools."""
        cursor = db.execute('SELECT * FROM schools ORDER BY name')
        schools = []
        for row in cursor.fetchall():
            school = cls()
            school.id = row['id']
            school.name = row['name']
            school.address = row['address']
            school.phone = row['phone']
            school.fax = row['fax']
            school.hours = row['hours']
            school.schedule_type = row['schedule_type']
            school.current_extension = row['current_extension']
            school.created_at = row['created_at']
            schools.append(school)
        return schools
    
    @classmethod
    def get_by_id(cls, db, school_id):
        """Get school by ID."""
        cursor = db.execute('SELECT * FROM schools WHERE id = ?', (school_id,))
        row = cursor.fetchone()
        if row:
            school = cls()
            school.id = row['id']
            school.name = row['name']
            school.address = row['address']
            school.phone = row['phone']
            school.fax = row['fax']
            school.hours = row['hours']
            school.schedule_type = row['schedule_type']
            school.current_extension = row['current_extension']
            school.created_at = row['created_at']
            return school
        return None
    
    def save(self, db):
        """Save school to database."""
        if self.id:
            # Update existing
            db.execute('''
                UPDATE schools 
                SET name=?, address=?, phone=?, fax=?, hours=?, 
                    schedule_type=?, current_extension=?
                WHERE id=?
            ''', (self.name, self.address, self.phone, self.fax, self.hours,
                  self.schedule_type, self.current_extension, self.id))
        else:
            # Create new
            cursor = db.execute('''
                INSERT INTO schools (name, address, phone, fax, hours, schedule_type, current_extension)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.name, self.address, self.phone, self.fax, self.hours,
                  self.schedule_type, self.current_extension))
            self.id = cursor.lastrowid
        db.commit()
    
    def get_schedule(self):
        """Get the current schedule for this school."""
        if self.schedule_type == 'thomas_stone':
            return get_thomas_stone_schedule(self.current_extension)
        return None


class StudentSchedule:
    """Link students to schools and track their class schedules."""
    def __init__(self, id=None, student_id=None, school_id=None, lunch_type='A',
                 classes=None, created_at=None):
        self.id = id
        self.student_id = student_id
        self.school_id = school_id
        self.lunch_type = lunch_type
        self.classes = classes or {}  # JSON field for period -> class mapping
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def create_table(cls, db):
        """Create the student_schedules table."""
        db.execute('''
            CREATE TABLE IF NOT EXISTS student_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                lunch_type TEXT DEFAULT 'A',
                classes TEXT,  -- JSON string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (school_id) REFERENCES schools (id)
            )
        ''')
        db.commit()
    
    @classmethod
    def get_by_student(cls, db, student_id):
        """Get schedule for a student."""
        cursor = db.execute('''
            SELECT * FROM student_schedules WHERE student_id = ?
        ''', (student_id,))
        row = cursor.fetchone()
        if row:
            import json
            schedule = cls()
            schedule.id = row['id']
            schedule.student_id = row['student_id']
            schedule.school_id = row['school_id']
            schedule.lunch_type = row['lunch_type']
            schedule.classes = json.loads(row['classes']) if row['classes'] else {}
            schedule.created_at = row['created_at']
            return schedule
        return None
    
    def save(self, db):
        """Save schedule to database."""
        import json
        classes_json = json.dumps(self.classes)
        
        if self.id:
            # Update existing
            db.execute('''
                UPDATE student_schedules 
                SET school_id=?, lunch_type=?, classes=?
                WHERE id=?
            ''', (self.school_id, self.lunch_type, classes_json, self.id))
        else:
            # Create new
            cursor = db.execute('''
                INSERT INTO student_schedules (student_id, school_id, lunch_type, classes)
                VALUES (?, ?, ?, ?)
            ''', (self.student_id, self.school_id, self.lunch_type, classes_json))
            self.id = cursor.lastrowid
        db.commit()


# Thomas Stone High School schedule data
def get_thomas_stone_schedule(extension_type='regular'):
    """Get Thomas Stone High School schedule based on extension type."""
    
    schedules = {
        'regular': {
            'name': "No Extension",
            'periods': [
                {'number': 1, 'start': '7:30', 'end': '8:20'},
                {'number': 2, 'start': '8:24', 'end': '9:14'},
                {'number': 3, 'start': '9:18', 'end': '10:08'},
                {'number': 4, 'start': '10:12', 'end': '11:02'},
                {'number': 5, 'start': '11:02', 'end': '11:32', 'lunch_type': 'A', 'is_lunch': True},
                {'number': 5, 'start': '11:06', 'end': '11:56', 'lunch_type': 'B'},
                {'number': 6, 'start': '11:36', 'end': '12:26', 'lunch_type': 'A'},
                {'number': 6, 'start': '11:56', 'end': '12:26', 'lunch_type': 'B', 'is_lunch': True},
                {'number': 7, 'start': '12:30', 'end': '1:20'},
                {'number': 8, 'start': '1:24', 'end': '2:15'}
            ]
        },
        'extension1': {
            'name': "1st Period Extension",
            'periods': [
                {'number': 1, 'start': '7:30', 'end': '8:21'},
                {'number': '1-EXT', 'start': '8:21', 'end': '8:51', 'is_extension': True},
                {'number': 2, 'start': '8:55', 'end': '9:40'},
                {'number': 3, 'start': '9:44', 'end': '10:29'},
                {'number': 4, 'start': '10:33', 'end': '11:18'},
                {'number': 5, 'start': '11:18', 'end': '11:48', 'lunch_type': 'A', 'is_lunch': True},
                {'number': 5, 'start': '11:22', 'end': '12:07', 'lunch_type': 'B'},
                {'number': 6, 'start': '11:52', 'end': '12:37', 'lunch_type': 'A'},
                {'number': 6, 'start': '12:07', 'end': '12:37', 'lunch_type': 'B', 'is_lunch': True},
                {'number': 7, 'start': '12:41', 'end': '1:26'},
                {'number': 8, 'start': '1:30', 'end': '2:15'}
            ]
        },
        'extension2': {
            'name': "2nd Period Extension",
            'periods': [
                {'number': 1, 'start': '7:30', 'end': '8:21'},
                {'number': 2, 'start': '8:25', 'end': '9:10'},
                {'number': '2-EXT', 'start': '9:10', 'end': '9:40', 'is_extension': True},
                {'number': 3, 'start': '9:44', 'end': '10:29'},
                {'number': 4, 'start': '10:33', 'end': '11:18'},
                {'number': 5, 'start': '11:18', 'end': '11:48', 'lunch_type': 'A', 'is_lunch': True},
                {'number': 5, 'start': '11:22', 'end': '12:07', 'lunch_type': 'B'},
                {'number': 6, 'start': '11:52', 'end': '12:37', 'lunch_type': 'A'},
                {'number': 6, 'start': '12:07', 'end': '12:37', 'lunch_type': 'B', 'is_lunch': True},
                {'number': 7, 'start': '12:41', 'end': '1:26'},
                {'number': 8, 'start': '1:30', 'end': '2:15'}
            ]
        },
        # Add more extensions as needed
        'early_dismissal': {
            'name': "Early Dismissal",
            'periods': [
                {'number': 1, 'start': '7:30', 'end': '8:05'},
                {'number': 2, 'start': '8:09', 'end': '8:42'},
                {'number': 3, 'start': '8:46', 'end': '9:19'},
                {'number': 4, 'start': '9:23', 'end': '9:56'},
                {'number': 5, 'start': '10:00', 'end': '10:30', 'lunch_type': 'A', 'is_lunch': True},
                {'number': 6, 'start': '10:34', 'end': '11:04', 'lunch_type': 'A'},
                {'number': 5, 'start': '10:00', 'end': '10:30', 'lunch_type': 'B'},
                {'number': 6, 'start': '10:34', 'end': '11:04', 'lunch_type': 'B', 'is_lunch': True},
                {'number': 7, 'start': '11:08', 'end': '11:39'},
                {'number': 8, 'start': '11:43', 'end': '12:15'}
            ]
        }
    }
    
    return schedules.get(extension_type, schedules['regular'])