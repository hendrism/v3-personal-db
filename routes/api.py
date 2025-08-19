from flask import Blueprint, jsonify
from datetime import date
from database import get_db
from models import Student, Session, Goal, Objective

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/students/<int:student_id>/objectives')
def api_student_objectives(student_id):
    db = get_db()
    objectives = Objective.get_by_student(db, student_id)
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

@api_bp.route('/objectives/<int:objective_id>/progress')
def api_objective_progress(objective_id):
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

@api_bp.route('/students')
def api_students():
    db = get_db()
    students = Student.get_all(db)
    return jsonify([s.to_dict() for s in students])

@api_bp.route('/sessions/today')
def api_todays_sessions():
    db = get_db()
    today = date.today()
    sessions = Session.get_by_date(db, today)
    return jsonify([s.to_dict() for s in sessions])

@api_bp.route('/goals/<int:student_id>')
def api_student_goals(student_id):
    db = get_db()
    goals = Goal.get_by_student(db, student_id)
    return jsonify([g.to_dict() for g in goals])
