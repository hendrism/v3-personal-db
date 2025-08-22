from flask import Flask
from database import init_db
from routes import (
    dashboard_bp,
    students_bp,
    sessions_bp,
    api_bp,
    admin_bp,
)
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-dev-key'

with app.app_context():
    init_db()

app.register_blueprint(dashboard_bp)
app.register_blueprint(students_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)
