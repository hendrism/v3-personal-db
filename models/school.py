from datetime import datetime
import json


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
            db.execute('''
                UPDATE schools
                SET name=?, address=?, phone=?, fax=?, hours=?,
                    schedule_type=?, current_extension=?
                WHERE id=?
            ''', (self.name, self.address, self.phone, self.fax, self.hours,
                  self.schedule_type, self.current_extension, self.id))
        else:
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
        self.classes = classes or {}
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
                classes TEXT,
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
        classes_json = json.dumps(self.classes)

        if self.id:
            db.execute('''
                UPDATE student_schedules
                SET school_id=?, lunch_type=?, classes=?
                WHERE id=?
            ''', (self.school_id, self.lunch_type, classes_json, self.id))
        else:
            cursor = db.execute('''
                INSERT INTO student_schedules (student_id, school_id, lunch_type, classes)
                VALUES (?, ?, ?, ?)
            ''', (self.student_id, self.school_id, self.lunch_type, classes_json))
            self.id = cursor.lastrowid
        db.commit()


# Thomas Stone High School schedule data
# (unchanged from original models.py)
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
