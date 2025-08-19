from flask import Blueprint, render_template, request, redirect, url_for
from database import get_db
from models import School, get_thomas_stone_schedule
import json

schools_bp = Blueprint('schools', __name__)

@schools_bp.route('/schools')
def schools():
    db = get_db()
    schools = School.get_all(db)
    return render_template('schools.html', schools=schools)

@schools_bp.route('/schools/<int:school_id>')
def school_detail(school_id):
    db = get_db()
    school = School.get_by_id(db, school_id)
    if not school:
        return "School not found", 404
    cursor = db.execute('''
        SELECT s.*, ss.lunch_type, ss.classes, ss.room_numbers
        FROM students s
        JOIN student_schedules ss ON s.id = ss.student_id
        WHERE ss.school_id = ?
        ORDER BY s.last_name, s.first_name
    ''', (school_id,))
    students = []
    for row in cursor.fetchall():
        student_data = {
            'id': row['id'],
            'full_name': f"{row['first_name']} {row['last_name']}",
            'lunch_type': row['lunch_type'],
            'classes': json.loads(row['classes']) if row['classes'] else {},
            'room_numbers': json.loads(row['room_numbers']) if row['room_numbers'] else {}
        }
        students.append(student_data)
    schedule = None
    if school.schedule_type == 'thomas_stone':
        schedule = get_thomas_stone_schedule(school.current_extension)
    return render_template('school_detail.html', school=school, schedule=schedule, students=students)

@schools_bp.route('/schools/new', methods=['GET', 'POST'])
def new_school():
    if request.method == 'POST':
        school = School(
            name=request.form['name'],
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            fax=request.form.get('fax'),
            hours=request.form.get('hours'),
            schedule_type=request.form.get('schedule_type', 'simple')
        )
        db = get_db()
        school.save(db)
        return redirect(url_for('schools.schools'))
    return render_template('school_form.html')

@schools_bp.route('/schools/<int:school_id>/schedule', methods=['POST'])
def update_school_schedule(school_id):
    db = get_db()
    school = School.get_by_id(db, school_id)
    if not school:
        return "School not found", 404
    school.current_extension = request.form['extension_type']
    school.save(db)
    return redirect(url_for('schools.school_detail', school_id=school_id))
