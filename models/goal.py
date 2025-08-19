from .base import BaseModel


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

    def get_objectives(self, db):
        """Get all objectives for this goal."""
        return Objective.get_by_goal(db, self.id)

    def get_current_progress(self, db):
        """Calculate current progress for this goal based on all objectives."""
        objectives = self.get_objectives(db)
        if not objectives:
            return 0

        total_progress = sum(obj.get_current_progress(db) for obj in objectives)
        return round(total_progress / len(objectives), 1)

    @classmethod
    def create(cls, db, data):
        cursor = db.execute('''
            INSERT INTO goals (student_id, description, target_accuracy)
            VALUES (?, ?, ?)
        ''', (data['student_id'], data['description'], data.get('target_accuracy', 80)))

        goal_id = cursor.lastrowid
        db.commit()
        return cls.get_by_id(db, goal_id)


class Objective(BaseModel):
    """Objectives belong to goals."""
    table_name = 'objectives'

    def __init__(self, id=None, goal_id=None, description='', target_percentage=80,
                 notes='', active=True, created_at=None):
        self.id = id
        self.goal_id = goal_id
        self.description = description
        self.target_percentage = target_percentage
        self.notes = notes
        self.active = active
        self.created_at = created_at

    @classmethod
    def get_by_goal(cls, db, goal_id):
        """Get all objectives for a specific goal."""
        cursor = db.execute("SELECT * FROM objectives WHERE goal_id = ? AND active = 1", (goal_id,))
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_by_student(cls, db, student_id):
        """Get all objectives for a student (across all goals)."""
        cursor = db.execute('''
            SELECT o.* FROM objectives o
            JOIN goals g ON o.goal_id = g.id
            WHERE g.student_id = ? AND o.active = 1 AND g.active = 1
            ORDER BY g.id, o.id
        ''', (student_id,))
        return [cls.from_row(row) for row in cursor.fetchall()]

    def get_goal(self, db):
        """Get the goal this objective belongs to."""
        return Goal.get_by_id(db, self.goal_id)

    def get_current_progress(self, db):
        """Calculate current progress percentage based on recent trial logs."""
        cursor = db.execute('''
            SELECT independent, minimal_support, moderate_support, maximal_support, incorrect
            FROM trial_logs tl
            JOIN sessions s ON tl.session_id = s.id
            WHERE tl.objective_id = ? AND s.session_date >= date('now', '-30 days')
        ''', (self.id,))

        trials = cursor.fetchall()
        if not trials:
            return 0

        total_trials = 0
        total_independent = 0

        for trial in trials:
            trial_total = sum(trial)
            total_trials += trial_total
            total_independent += trial[0]  # independent is first column

        if total_trials == 0:
            return 0

        return round((total_independent / total_trials) * 100, 1)

    def get_trial_logs(self, db, limit=None):
        """Get recent trial logs for this objective."""
        from .session import TrialLog

        query = '''
            SELECT tl.* FROM trial_logs tl
            JOIN sessions s ON tl.session_id = s.id
            WHERE tl.objective_id = ?
            ORDER BY s.session_date DESC, tl.created_at DESC
        '''
        params = [self.id]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = db.execute(query, params)
        return [TrialLog.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def create(cls, db, data):
        cursor = db.execute('''
            INSERT INTO objectives (goal_id, description, target_percentage, notes)
            VALUES (?, ?, ?, ?)
        ''', (data['goal_id'], data['description'],
              data.get('target_percentage', 80), data.get('notes', '')))

        objective_id = cursor.lastrowid
        db.commit()
        return cls.get_by_id(db, objective_id)
