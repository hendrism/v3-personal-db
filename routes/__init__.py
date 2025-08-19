from .dashboard import dashboard_bp
from .students import students_bp
from .sessions import sessions_bp
from .schools import schools_bp
from .api import api_bp
from .admin import admin_bp

__all__ = [
    'dashboard_bp',
    'students_bp',
    'sessions_bp',
    'schools_bp',
    'api_bp',
    'admin_bp',
]
