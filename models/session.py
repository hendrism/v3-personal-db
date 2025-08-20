from datetime import datetime, date, timedelta

from .base import BaseModel


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

        if isinstance(self.session_date, str):
            session_date = datetime.strptime(
                self.session_date, '%Y-%m-%d').date()
        else:
            session_date = self.session_date

        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        return start_of_week <= session_date <= end_of_week

    def get_student(self, db):
        """Get the student for this session."""
        from .student import Student
        return Student.get_by_id(db, self.student_id)

    def get_trial_logs(self, db):
        """Get all trial logs for this session."""
        return TrialLog.get_by_session(db, self.id)

    @classmethod
    def get_recent(cls, db, limit=10):
        cursor = db.execute(
            "SELECT * FROM sessions ORDER BY session_date DESC, created_at DESC LIMIT ?", (limit,))
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_upcoming(cls, db, days=7):
        cursor = db.execute('''
            SELECT * FROM sessions
            WHERE session_date BETWEEN date('now') AND date('now', '+{} days')
            ORDER BY session_date ASC
        '''.format(days))
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_by_student(cls, db, student_id):
        cursor = db.execute(
            "SELECT * FROM sessions WHERE student_id = ? ORDER BY session_date DESC", (student_id,))
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_pending_soap_notes(cls, db):
        cursor = db.execute('''
            SELECT * FROM sessions s
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
    # Add these methods to the Session class in models/session.py


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


class TrialLog(BaseModel):
    """Enhanced trial log - now links to objectives."""
    table_name = 'trial_logs'
    
    # Support levels in order from most to least independent
    SUPPORT_LEVELS = ['independent', 'minimal_support', 'moderate_support', 'maximal_support']

    def __init__(self, id=None, session_id=None, objective_id=None, goal_id=None,
                 independent=0, minimal_support=0, moderate_support=0, maximal_support=0,
                 incorrect=0, notes='', created_at=None):
        self.id = id
        self.session_id = session_id
        self.objective_id = objective_id
        self.goal_id = goal_id  # Keep for backward compatibility
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
    
    def total_trials_new(self):
        """Calculate the total number of trials recorded using new columns."""
        return (
            (self.independent or 0) +
            (self.minimal_support or 0) +
            (self.moderate_support or 0) +
            (self.maximal_support or 0) +
            (self.incorrect or 0)
        )

    def percent_independent(self):
        """Calculate the percentage of trials that were independent."""
        total = self.total_trials_new()
        return round(((self.independent or 0) / total) * 100, 1) if total > 0 else 0

    def percent_minimal_support(self):
        """Calculate the percentage of trials with minimal support."""
        total = self.total_trials_new()
        return round(((self.minimal_support or 0) / total) * 100, 1) if total > 0 else 0

    def percent_moderate_support(self):
        """Calculate the percentage of trials with moderate support."""
        total = self.total_trials_new()
        return round(((self.moderate_support or 0) / total) * 100, 1) if total > 0 else 0

    def percent_maximal_support(self):
        """Calculate the percentage of trials with maximal support."""
        total = self.total_trials_new()
        return round(((self.maximal_support or 0) / total) * 100, 1) if total > 0 else 0

    def percent_incorrect(self):
        """Calculate the percentage of trials that were incorrect."""
        total = self.total_trials_new()
        return round(((self.incorrect or 0) / total) * 100, 1) if total > 0 else 0

    def percent_correct_up_to(self, support_level):
        """
        Return percent correct at or below the specified support level.
        support_level: str, one of 'independent', 'minimal_support', 'moderate_support', 'maximal_support'
        """
        total = self.total_trials_new()
        if total == 0 or support_level not in self.SUPPORT_LEVELS:
            return 0.0
        idx = self.SUPPORT_LEVELS.index(support_level) + 1
        correct_sum = sum((getattr(self, lvl) or 0) for lvl in self.SUPPORT_LEVELS[:idx])
        return round((correct_sum / total) * 100, 1)

    def get_objective(self, db):
        """Get the objective this trial log is for."""
        if self.objective_id:
            from .goal import Objective
            return Objective.get_by_id(db, self.objective_id)
        return None

    def get_goal(self, db):
        """Get the goal (either directly or through objective)."""
        if self.objective_id:
            objective = self.get_objective(db)
            return objective.get_goal(db) if objective else None
        elif self.goal_id:
            from .goal import Goal
            return Goal.get_by_id(db, self.goal_id)
        return None

    def get_session(self, db):
        """Get the session this trial log belongs to."""
        return Session.get_by_id(db, self.session_id)

    @classmethod
    def get_by_session(cls, db, session_id):
        cursor = db.execute(
            "SELECT * FROM trial_logs WHERE session_id = ?", (session_id,))
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
    def get_by_objective(cls, db, objective_id, limit=None):
        """Get trial logs for a specific objective."""
        query = '''
            SELECT tl.* FROM trial_logs tl
            JOIN sessions s ON tl.session_id = s.id
            WHERE tl.objective_id = ?
            ORDER BY s.session_date DESC, tl.created_at DESC
        '''
        params = [objective_id]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = db.execute(query, params)
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def create(cls, db, data):
        cursor = db.execute('''
            INSERT INTO trial_logs (session_id, objective_id, goal_id, independent,
                                  minimal_support, moderate_support, maximal_support,
                                  incorrect, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['session_id'], data.get('objective_id'), data.get('goal_id'),
              data.get('independent', 0), data.get('minimal_support', 0),
              data.get('moderate_support', 0), data.get('maximal_support', 0),
              data.get('incorrect', 0), data.get('notes', '')))

        trial_id = cursor.lastrowid
        db.commit()
        return cls.get_by_id(db, trial_id)

    # Add these methods to the Session class in models/session.py
