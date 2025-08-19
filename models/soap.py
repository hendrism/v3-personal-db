from .base import BaseModel


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

    def get_session(self, db):
        from .session import Session
        return Session.get_by_id(db, self.session_id)

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
        from .session import TrialLog

        trials = TrialLog.get_by_session(db, session.id)

        subjective = f"Student participated in {session.session_type.lower()} therapy session."

        objective = "Trial data collected:\n"
        for trial in trials:
            if trial.objective_id:
                objective_obj = trial.get_objective(db)
                if objective_obj:
                    objective += f"- {objective_obj.description}: {trial.independence_percentage}% independent\n"
            else:
                objective += f"- {trial.total_trials} trials, {trial.independence_percentage}% independence\n"

        assessment = (
            "Student demonstrated varying levels of support needs across targeted skills."
        )

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
            db.execute('''
                UPDATE soap_notes
                SET subjective = ?, objective = ?, assessment = ?, plan = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (data['subjective'], data['objective'], data['assessment'],
                  data['plan'], data['session_id']))
            db.commit()
            return cls.get_by_session(db, data['session_id'])
        else:
            cursor = db.execute('''
                INSERT INTO soap_notes (session_id, subjective, objective, assessment, plan)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['session_id'], data['subjective'], data['objective'],
                  data['assessment'], data['plan']))

            soap_id = cursor.lastrowid
            db.commit()
            return cls.get_by_id(db, soap_id)
