from .connection import get_db_connection


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

