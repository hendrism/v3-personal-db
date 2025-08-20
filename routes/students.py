from flask import Blueprint, render_template, request, redirect, url_for
from database import get_db
from models import Student, Session, Goal, Objective, TrialLog, SOAPNote, School, StudentSchedule

students_bp = Blueprint('students', __name__)

@students_bp.route('/students')
def students():
    """List all students."""
    db = get_db()
    students = Student.get_all(db)
    return render_template('students.html', students=students)

@students_bp.route('/students/<int:student_id>')
def student_detail(student_id):
    """Individual student view with goals and objectives."""
    db = get_db()
    student = Student.get_by_id(db, student_id)
    if not student:
        return "Student not found", 404

    # Get all related data
    sessions = Session.get_by_student(db, student_id)
    goals = Goal.get_by_student(db, student_id)

    # Enhanced: Get goals with their objectives and calculate progress
    goals_with_objectives = []
    for goal in goals:
        objectives = goal.get_objectives(db)
        for objective in objectives:
            objective.current_progress = objective.get_current_progress(db)
        goals_with_objectives.append({'goal': goal,'objectives': objectives,'progress': goal.get_current_progress(db)})

    recent_trials = TrialLog.get_recent_by_student(db, student_id, limit=10)
    for trial in recent_trials:
        if trial.objective_id:
            objective = trial.get_objective(db)
            trial.objective_description = objective.description if objective else None
        else:
            trial.objective_description = None

    soap_notes = SOAPNote.get_by_student(db, student_id)
    for soap in soap_notes:
        session = soap.get_session(db)
        soap.session_date = session.session_date if session else 'Unknown'

    student_schedule = StudentSchedule.get_by_student(db, student_id)
    schools = {school.id: school for school in School.get_all(db)}

    return render_template('student_detail.html', student=student, sessions=sessions, goals=goals,
                           goals_with_objectives=goals_with_objectives, recent_trials=recent_trials,
                           soap_notes=soap_notes, student_schedule=student_schedule, schools=schools)

@students_bp.route('/students/new', methods=['GET', 'POST'])
def new_student():
    """Add new student."""
    if request.method == 'POST':
        db = get_db()
        student_data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'grade_level': request.form.get('grade_level'),
            'preferred_name': request.form.get('preferred_name'),
            'pronouns': request.form.get('pronouns'),
            'notes': request.form.get('notes')
        }
        student = Student.create(db, student_data)
        return redirect(url_for('students.student_detail', student_id=student.id))
    return render_template('student_form.html')

@students_bp.route('/students/<int:student_id>/goals/new', methods=['GET', 'POST'])
def new_goal(student_id):
    db = get_db()
    student = Student.get_by_id(db, student_id)
    if not student:
        return "Student not found", 404
    if request.method == 'POST':
        goal_data = {
            'student_id': student_id,
            'description': request.form['description'],
            'target_accuracy': int(request.form.get('target_accuracy', 80))
        }
        Goal.create(db, goal_data)
        return redirect(url_for('students.student_detail', student_id=student_id))
    return render_template('goal_form.html', student=student)

@students_bp.route('/goals/<int:goal_id>/objectives/new', methods=['GET', 'POST'])
def new_objective(goal_id):
    db = get_db()
    goal = Goal.get_by_id(db, goal_id)
    if not goal:
        return "Goal not found", 404
    student = Student.get_by_id(db, goal.student_id)
    if request.method == 'POST':
        objective_data = {
            'goal_id': goal_id,
            'description': request.form['description'],
            'target_percentage': int(request.form.get('target_percentage', 80)),
            'notes': request.form.get('notes', '')
        }
        Objective.create(db, objective_data)
        return redirect(url_for('students.student_detail', student_id=goal.student_id))
    return render_template('objective_form.html', goal=goal, student=student)

@students_bp.route('/students/<int:student_id>/schedule', methods=['GET', 'POST'])
def student_schedule(student_id):
    db = get_db()
    student = Student.get_by_id(db, student_id)
    if not student:
        return "Student not found", 404
    schedule = StudentSchedule.get_by_student(db, student_id)
    schools = School.get_all(db)
    if request.method == 'POST':
        if not schedule:
            schedule = StudentSchedule(student_id=student_id)
        schedule.school_id = request.form['school_id']
        schedule.lunch_type = request.form.get('lunch_type', 'A')
        classes = {}
        for period in range(1,9):
            class_name = request.form.get(f'period_{period}', '').strip()
            room_number = request.form.get(f'room_{period}', '').strip()
            if class_name or room_number:
                classes[str(period)] = {
                    'name': class_name,
                    'room': room_number
                }
        schedule.classes = classes
        schedule.save(db)
        return redirect(url_for('students.student_detail', student_id=student_id))
    return render_template('student_schedule_form.html', student=student, schedule=schedule, schools=schools)


@students_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
def edit_goal(goal_id):
    db = get_db()
    goal = Goal.get_by_id(db, goal_id)
    if not goal:
        return "Goal not found", 404

    student = Student.get_by_id(db, goal.student_id)

    if request.method == 'POST':
        # Update goal logic here
        goal.description = request.form['description']
        goal.target_accuracy = int(request.form.get('target_accuracy', 80))
        # Add save method to Goal model or use direct SQL
        return redirect(url_for('students.student_detail', student_id=goal.student_id))

    return render_template('goal_form.html', goal=goal, student=student, edit_mode=True)


@students_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
def delete_goal(goal_id):
    db = get_db()
    goal = Goal.get_by_id(db, goal_id)
    if not goal:
        return "Goal not found", 404

    student_id = goal.student_id

    # Delete goal and all its objectives and trial logs
    db.execute(
        'DELETE FROM trial_logs WHERE objective_id IN (SELECT id FROM objectives WHERE goal_id = ?)', (goal_id,))
    db.execute('DELETE FROM objectives WHERE goal_id = ?', (goal_id,))
    db.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
    db.commit()

    return redirect(url_for('students.student_detail', student_id=student_id))


@students_bp.route('/objectives/<int:objective_id>/edit', methods=['GET', 'POST'])
def edit_objective(objective_id):
    db = get_db()
    objective = Objective.get_by_id(db, objective_id)
    if not objective:
        return "Objective not found", 404

    goal = objective.get_goal(db)
    student = Student.get_by_id(db, goal.student_id)

    if request.method == 'POST':
        # Update objective logic here
        objective.description = request.form['description']
        objective.target_percentage = int(
            request.form.get('target_percentage', 80))
        objective.notes = request.form.get('notes', '')
        # Add save method or use direct SQL
        return redirect(url_for('students.student_detail', student_id=goal.student_id))

    return render_template('objective_form.html', objective=objective, goal=goal, student=student, edit_mode=True)


@students_bp.route('/objectives/<int:objective_id>/delete', methods=['POST'])
def delete_objective(objective_id):
    db = get_db()
    objective = Objective.get_by_id(db, objective_id)
    if not objective:
        return "Objective not found", 404

    goal = objective.get_goal(db)
    student_id = goal.student_id

    # Delete objective and all its trial logs
    db.execute('DELETE FROM trial_logs WHERE objective_id = ?', (objective_id,))
    db.execute('DELETE FROM objectives WHERE id = ?', (objective_id,))
    db.commit()

    return redirect(url_for('students.student_detail', student_id=student_id))
