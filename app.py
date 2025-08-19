# app.py - Complete Enhanced Version with Objectives Support
from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import init_db, get_db, add_sample_data
from models import Student, Session, Goal, Objective, TrialLog, SOAPNote, School, StudentSchedule, get_thomas_stone_schedule
import json
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-dev-key'  # Simple since it's local only

# Initialize database on startup
with app.app_context():
    init_db()

@app.route('/')
def dashboard():
    """Main dashboard - overview of everything."""
    db = get_db()
    
    # Get recent activity
    recent_sessions = Session.get_recent(db, limit=5)
    active_students = Student.get_active(db)
    pending_soap_notes = Session.get_pending_soap_notes(db)
    upcoming_sessions = Session.get_upcoming(db, days=7)
    
    # School data
    schools = School.get_all(db)
    recent_schools = []
    for school in schools[:3]:  # Show top 3 schools
        # Count students at this school
        cursor = db.execute('SELECT COUNT(*) FROM student_schedules WHERE school_id = ?', (school.id,))
        student_count = cursor.fetchone()[0]
        recent_schools.append({
            'school': school,
            'student_count': student_count
        })
    
    stats = {
        'total_students': len(active_students),
        'total_schools': len(schools),
        'sessions_this_week': len([s for s in recent_sessions if s.this_week()]),
        'pending_soap_notes': len(pending_soap_notes),
        'upcoming_sessions': len(upcoming_sessions)
    }
    
    return render_template('dashboard.html', 
                         stats=stats,
                         recent_sessions=recent_sessions,
                         pending_soap_notes=pending_soap_notes,
                         upcoming_sessions=upcoming_sessions,
                         recent_schools=recent_schools)

# Students
@app.route('/students')
def students():
    """List all students."""
    db = get_db()
    students = Student.get_all(db)
    return render_template('students.html', students=students)

@app.route('/students/<int:student_id>')
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
        # Add current progress to each objective
        for objective in objectives:
            objective.current_progress = objective.get_current_progress(db)
        
        goals_with_objectives.append({
            'goal': goal,
            'objectives': objectives,
            'progress': goal.get_current_progress(db)
        })
    
    # Get recent trials and add objective descriptions
    recent_trials = TrialLog.get_recent_by_student(db, student_id, limit=10)
    for trial in recent_trials:
        if trial.objective_id:
            objective = trial.get_objective(db)
            trial.objective_description = objective.description if objective else None
        else:
            trial.objective_description = None
    
    # Get SOAP notes and add session dates
    soap_notes = SOAPNote.get_by_student(db, student_id)
    for soap in soap_notes:
        session = soap.get_session(db)
        soap.session_date = session.session_date if session else 'Unknown'
    
    student_schedule = StudentSchedule.get_by_student(db, student_id)
    schools = {school.id: school for school in School.get_all(db)}
    
    return render_template('student_detail.html',
                         student=student,
                         sessions=sessions,
                         goals=goals,  # Keep for backward compatibility
                         goals_with_objectives=goals_with_objectives,  # New enhanced data
                         recent_trials=recent_trials,
                         soap_notes=soap_notes,
                         student_schedule=student_schedule,
                         schools=schools)

@app.route('/students/new', methods=['GET', 'POST'])
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
        return redirect(url_for('student_detail', student_id=student.id))
    
    return render_template('student_form.html')

# Goals and Objectives (NEW ROUTES)
@app.route('/students/<int:student_id>/goals/new', methods=['GET', 'POST'])
def new_goal(student_id):
    """Add new goal for student."""
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
        
        goal = Goal.create(db, goal_data)
        return redirect(url_for('student_detail', student_id=student_id))
    
    return render_template('goal_form.html', student=student)

@app.route('/goals/<int:goal_id>/objectives/new', methods=['GET', 'POST'])
def new_objective(goal_id):
    """Add new objective to a goal."""
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
        
        objective = Objective.create(db, objective_data)
        return redirect(url_for('student_detail', student_id=goal.student_id))
    
    return render_template('objective_form.html', goal=goal, student=student)

# Sessions
@app.route('/sessions')
def sessions():
    """List sessions with filtering."""
    db = get_db()
    date_filter = request.args.get('date')
    if date_filter:
        sessions = Session.get_by_date_with_student_info(db, date_filter)
    else:
        sessions = Session.get_recent_with_student_info(db, limit=20)
    
    today = date.today().isoformat()
    return render_template('sessions.html', sessions=sessions, today=today)

@app.route('/sessions/new', methods=['GET', 'POST'])
def new_session():
    """Quick session entry."""
    db = get_db()
    if request.method == 'POST':
        session_data = {
            'student_id': request.form['student_id'],
            'session_date': request.form['session_date'],
            'start_time': request.form.get('start_time'),
            'end_time': request.form.get('end_time'),
            'session_type': request.form.get('session_type', 'Individual'),
            'location': request.form.get('location'),
            'notes': request.form.get('notes')
        }
        session = Session.create(db, session_data)
        return redirect(url_for('session_detail', session_id=session.id))
    
    students = Student.get_active(db)
    return render_template('session_form.html', students=students)

@app.route('/sessions/<int:session_id>')
def session_detail(session_id):
    """Enhanced session detail with objective-based trial entry."""
    db = get_db()
    session = Session.get_by_id(db, session_id)
    if not session:
        return "Session not found", 404
    
    student = Student.get_by_id(db, session.student_id)
    
    # Get goals and objectives for this student
    goals = Goal.get_by_student(db, session.student_id)
    goals_with_objectives = []
    all_objectives = []
    
    for goal in goals:
        objectives = goal.get_objectives(db)
        goals_with_objectives.append({
            'goal': goal,
            'objectives': objectives
        })
        all_objectives.extend(objectives)
    
    trial_logs = TrialLog.get_by_session(db, session_id)
    # Add objective descriptions to trial logs
    for trial in trial_logs:
        if trial.objective_id:
            objective = trial.get_objective(db)
            trial.objective_description = objective.description if objective else None
    
    soap_note = SOAPNote.get_by_session(db, session_id)
    
    return render_template('session_detail.html',
                         session=session,
                         student=student,
                         goals=goals,  # Keep for backward compatibility
                         goals_with_objectives=goals_with_objectives,
                         all_objectives=all_objectives,
                         trial_logs=trial_logs,
                         soap_note=soap_note)

# Enhanced Trial Data Entry
@app.route('/trials/new', methods=['POST'])
def add_trial():
    """Enhanced trial data entry with objective support."""
    db = get_db()
    trial_data = {
        'session_id': request.form['session_id'],
        'objective_id': request.form.get('objective_id'),  # NEW: Link to objective
        'goal_id': request.form.get('goal_id'),  # Keep for backward compatibility
        'independent': int(request.form.get('independent', 0)),
        'minimal_support': int(request.form.get('minimal_support', 0)),
        'moderate_support': int(request.form.get('moderate_support', 0)),
        'maximal_support': int(request.form.get('maximal_support', 0)),
        'incorrect': int(request.form.get('incorrect', 0)),
        'notes': request.form.get('notes')
    }
    
    trial = TrialLog.create(db, trial_data)
    return jsonify(trial.to_dict())

@app.route('/trials/<int:trial_id>/edit', methods=['POST'])
def edit_trial(trial_id):
    """Edit existing trial data."""
    db = get_db()
    trial = TrialLog.get_by_id(db, trial_id)
    if not trial:
        return jsonify({'error': 'Trial not found'}), 404
    
    # Update trial data
    cursor = db.execute('''
        UPDATE trial_logs 
        SET independent = ?, minimal_support = ?, moderate_support = ?, 
            maximal_support = ?, incorrect = ?, notes = ?
        WHERE id = ?
    ''', (
        int(request.form.get('independent', 0)),
        int(request.form.get('minimal_support', 0)),
        int(request.form.get('moderate_support', 0)),
        int(request.form.get('maximal_support', 0)),
        int(request.form.get('incorrect', 0)),
        request.form.get('notes', ''),
        trial_id
    ))
    
    db.commit()
    updated_trial = TrialLog.get_by_id(db, trial_id)
    return jsonify(updated_trial.to_dict())

# SOAP Notes
@app.route('/soap/<int:session_id>')
def soap_note(session_id):
    """SOAP note for session."""
    db = get_db()
    session = Session.get_by_id(db, session_id)
    soap_note = SOAPNote.get_by_session(db, session_id)
    
    if not soap_note:
        # Auto-generate basic SOAP note from session data
        soap_note = SOAPNote.generate_from_session(db, session)
    
    return render_template('soap_note.html', 
                         session=session,
                         soap_note=soap_note)

@app.route('/soap/save', methods=['POST'])
def save_soap_note():
    """Save SOAP note."""
    db = get_db()
    soap_data = {
        'session_id': request.form['session_id'],
        'subjective': request.form.get('subjective'),
        'objective': request.form.get('objective'),
        'assessment': request.form.get('assessment'),
        'plan': request.form.get('plan')
    }
    
    soap_note = SOAPNote.create_or_update(db, soap_data)
    return jsonify({'success': True, 'id': soap_note.id})

# School Management Routes
@app.route('/schools')
def schools():
    db = get_db()
    schools = School.get_all(db)
    return render_template('schools.html', schools=schools)

@app.route('/schools/<int:school_id>')
def school_detail(school_id):
    db = get_db()
    school = School.get_by_id(db, school_id)
    if not school:
        return "School not found", 404
    
    # Get students at this school
    cursor = db.execute('''
        SELECT s.*, ss.lunch_type, ss.classes 
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
            'classes': json.loads(row['classes']) if row['classes'] else {}
        }
        students.append(student_data)
    
    # Get schedule if Thomas Stone
    schedule = None
    if school.schedule_type == 'thomas_stone':
        schedule = get_thomas_stone_schedule(school.current_extension)
    
    return render_template('school_detail.html', 
                         school=school, 
                         schedule=schedule,
                         students=students)

@app.route('/schools/new', methods=['GET', 'POST'])
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
        return redirect(url_for('schools'))
    
    return render_template('school_form.html')

@app.route('/schools/<int:school_id>/schedule', methods=['POST'])
def update_school_schedule(school_id):
    db = get_db()
    school = School.get_by_id(db, school_id)
    if not school:
        return "School not found", 404
    
    school.current_extension = request.form['extension_type']
    school.save(db)
    
    return redirect(url_for('school_detail', school_id=school_id))

@app.route('/students/<int:student_id>/schedule', methods=['GET', 'POST'])
def student_schedule(student_id):
    """Manage a student's schedule."""
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
        
        # Parse class schedule
        classes = {}
        for period in range(1, 9):
            class_name = request.form.get(f'period_{period}', '').strip()
            if class_name:
                classes[str(period)] = class_name
        schedule.classes = classes
        
        schedule.save(db)
        return redirect(url_for('student_detail', student_id=student_id))
    
    return render_template('student_schedule_form.html', 
                         student=student, 
                         schedule=schedule,
                         schools=schools)

# API endpoints for dynamic objective selection and existing functionality
@app.route('/api/students/<int:student_id>/objectives')
def api_student_objectives(student_id):
    """Get all objectives for a student (for dynamic selection)."""
    db = get_db()
    objectives = Objective.get_by_student(db, student_id)
    
    # Include goal information
    objectives_data = []
    for obj in objectives:
        goal = obj.get_goal(db)
        objectives_data.append({
            'id': obj.id,
            'description': obj.description,
            'target_percentage': obj.target_percentage,
            'goal_description': goal.description if goal else '',
            'current_progress': obj.get_current_progress(db)
        })
    
    return jsonify(objectives_data)

@app.route('/api/objectives/<int:objective_id>/progress')
def api_objective_progress(objective_id):
    """Get detailed progress for an objective."""
    db = get_db()
    objective = Objective.get_by_id(db, objective_id)
    if not objective:
        return jsonify({'error': 'Objective not found'}), 404
    
    recent_trials = objective.get_trial_logs(db, limit=10)
    
    return jsonify({
        'objective': objective.to_dict(),
        'current_progress': objective.get_current_progress(db),
        'recent_trials': [trial.to_dict() for trial in recent_trials]
    })

@app.route('/api/students')
def api_students():
    """Simple API for student list."""
    db = get_db()
    students = Student.get_all(db)
    return jsonify([s.to_dict() for s in students])

@app.route('/api/sessions/today')
def api_todays_sessions():
    """Today's sessions."""
    db = get_db()
    today = date.today()
    sessions = Session.get_by_date(db, today)
    return jsonify([s.to_dict() for s in sessions])

@app.route('/api/goals/<int:student_id>')
def api_student_goals(student_id):
    """Student's goals for trial entry."""
    db = get_db()
    goals = Goal.get_by_student(db, student_id)
    return jsonify([g.to_dict() for g in goals])

# Utility route for adding sample data
@app.route('/admin/add-sample-data')
def admin_add_sample_data():
    """Add sample data for testing."""
    try:
        add_sample_data()
        return jsonify({'success': True, 'message': 'Sample data added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Run in debug mode for development
    app.run(debug=True, host='127.0.0.1', port=5000)