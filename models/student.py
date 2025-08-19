from .base import BaseModel


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
