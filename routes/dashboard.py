from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from database import get_db
from models import Student, Session, School
from datetime import date, datetime, timedelta


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def dashboard():
    """Main dashboard - overview of everything."""
    db = get_db()

    # Get recent activity
    recent_sessions = Session.get_recent_with_student_info(db, limit=5)
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

    today = date.today().isoformat()

    return render_template('dashboard.html',
                         stats=stats,
                         recent_sessions=recent_sessions,
                         pending_soap_notes=pending_soap_notes,
                         upcoming_sessions=upcoming_sessions,
                         recent_schools=recent_schools,
                         today=today)


@dashboard_bp.route('/planner', methods=['GET', 'POST'])
def daily_planner():
    """Daily session planner interface."""
    db = get_db()
    
    # Get date from query param or default to today
    selected_date = request.args.get('date', date.today().isoformat())
    
    if request.method == 'POST':
        # Handle bulk session creation
        sessions_data = request.get_json()
        created_sessions = []
        
        for session_info in sessions_data['sessions']:
            # Create session for each student
            for student_id in session_info['student_ids']:
                session_data = {
                    'student_id': student_id,
                    'session_date': session_info['date'],
                    'start_time': session_info['start_time'],
                    'end_time': session_info['end_time'],
                    'session_type': 'Group' if len(session_info['student_ids']) > 1 else 'Individual',
                    'location': session_info.get('location', ''),
                    'notes': session_info.get('notes', ''),
                    'status': None
                }
                session = Session.create(db, session_data)
                created_sessions.append(session.to_dict())
        
        return jsonify({'success': True, 'sessions_created': len(created_sessions)})
    
    # Get existing sessions for the selected date
    existing_sessions = Session.get_by_date_with_student_info(db, selected_date)
    
    # Group sessions by time and type for display
    session_groups = {}
    for session in existing_sessions:
        key = f"{session.start_time or 'No time'}_{session.session_type}"
        if key not in session_groups:
            session_groups[key] = {
                'start_time': session.start_time,
                'end_time': session.end_time,
                'start_time_12h': session.start_time_12h,
                'end_time_12h': session.end_time_12h,
                'session_type': session.session_type,
                'location': session.location,
                'notes': session.notes,
                'students': [],
                'session_ids': []
            }
        session_groups[key]['students'].append({
            'name': session.student_name,
            'id': session.student_id
        })
        session_groups[key]['session_ids'].append(session.id)
    
    # Convert to list and sort by time
    grouped_sessions = list(session_groups.values())
    grouped_sessions.sort(key=lambda x: x['start_time'] or '99:99')
    
    # Get all active students for the planner
    students = Student.get_active(db)
    
    return render_template('daily_planner.html', 
                         selected_date=selected_date,
                         grouped_sessions=grouped_sessions,
                         students=students)


@dashboard_bp.route('/planner/start-session/<int:session_id>')
def start_session_tracking(session_id):
    """Start live tracking for a specific session."""
    # Redirect to live tracking with pre-filled session info
    return redirect(url_for('sessions.session_tracking', linked_session=session_id))

