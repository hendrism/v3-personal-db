from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import date
from database import get_db
from models import Student, Session, Goal, Objective, TrialLog, SOAPNote

sessions_bp = Blueprint('sessions', __name__)

@sessions_bp.route('/sessions')
def sessions():
    db = get_db()
    date_filter = request.args.get('date')
    if date_filter:
        sessions = Session.get_by_date_with_student_info(db, date_filter)
    else:
        sessions = Session.get_recent_with_student_info(db, limit=20)
    today = date.today().isoformat()
    return render_template('sessions.html', sessions=sessions, today=today)

@sessions_bp.route('/sessions/new', methods=['GET', 'POST'])
def new_session():
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
        return redirect(url_for('sessions.session_detail', session_id=session.id))
    students = Student.get_active(db)
    return render_template('session_form.html', students=students)

@sessions_bp.route('/sessions/<int:session_id>')
def session_detail(session_id):
    db = get_db()
    session = Session.get_by_id(db, session_id)
    if not session:
        return "Session not found", 404
    student = Student.get_by_id(db, session.student_id)
    goals = Goal.get_by_student(db, session.student_id)
    goals_with_objectives = []
    all_objectives = []
    for goal in goals:
        objectives = goal.get_objectives(db)
        goals_with_objectives.append({'goal': goal, 'objectives': objectives})
        all_objectives.extend(objectives)
    trial_logs = TrialLog.get_by_session(db, session_id)
    for trial in trial_logs:
        if trial.objective_id:
            objective = trial.get_objective(db)
            trial.objective_description = objective.description if objective else None
    soap_note = SOAPNote.get_by_session(db, session_id)
    return render_template('session_detail.html', session=session, student=student, goals=goals,
                           goals_with_objectives=goals_with_objectives, all_objectives=all_objectives,
                           trial_logs=trial_logs, soap_note=soap_note)

@sessions_bp.route('/trials/new', methods=['POST'])
def add_trial():
    db = get_db()
    trial_data = {
        'session_id': request.form['session_id'],
        'objective_id': request.form.get('objective_id'),
        'goal_id': request.form.get('goal_id'),
        'independent': int(request.form.get('independent', 0)),
        'minimal_support': int(request.form.get('minimal_support', 0)),
        'moderate_support': int(request.form.get('moderate_support', 0)),
        'maximal_support': int(request.form.get('maximal_support', 0)),
        'incorrect': int(request.form.get('incorrect', 0)),
        'notes': request.form.get('notes')
    }
    trial = TrialLog.create(db, trial_data)
    return jsonify(trial.to_dict())

@sessions_bp.route('/trials/<int:trial_id>/edit', methods=['POST'])
def edit_trial(trial_id):
    db = get_db()
    trial = TrialLog.get_by_id(db, trial_id)
    if not trial:
        return jsonify({'error': 'Trial not found'}), 404
    db.execute('''
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

@sessions_bp.route('/soap/<int:session_id>')
def soap_note(session_id):
    db = get_db()
    session = Session.get_by_id(db, session_id)
    soap_note = SOAPNote.get_by_session(db, session_id)
    if not soap_note:
        soap_note = SOAPNote.generate_from_session(db, session)
    return render_template('soap_note.html', session=session, soap_note=soap_note)

@sessions_bp.route('/soap/save', methods=['POST'])
def save_soap_note():
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
