from flask import Blueprint, render_template
from database import get_db
from models import Student, Session, School


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

    from datetime import date
    today = date.today().isoformat()

    return render_template('dashboard.html',
                         stats=stats,
                         recent_sessions=recent_sessions,
                         pending_soap_notes=pending_soap_notes,
                         upcoming_sessions=upcoming_sessions,
                         recent_schools=recent_schools,
                         today=today)

