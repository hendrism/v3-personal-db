from flask import Blueprint, jsonify
from database import add_sample_data

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/add-sample-data')
def admin_add_sample_data():
    """Add sample data for testing."""
    try:
        add_sample_data()
        return jsonify({'success': True, 'message': 'Sample data added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
