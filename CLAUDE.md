# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based student database application for managing therapy sessions, trial data, and SOAP notes. It's designed as a local-only application for organizing student information, goals, objectives, and session tracking.

## Setup and Development Commands

```bash
# Initial setup
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Run the application
python app.py
# Application runs on http://127.0.0.1:5000

# Initialize database with sample data
python database.py
```

## Architecture Overview

### Core Components

- **app.py**: Main Flask application entry point with blueprint registration
- **database.py**: SQLite database initialization, connection management, and schema definitions
- **models/**: SQLAlchemy-style model classes with database interaction methods
  - **base.py**: BaseModel class with common ORM functionality
  - Individual model files for Student, Session, Goal, Objective, SOAPNote, School, etc.
- **routes/**: Flask blueprint definitions organized by feature
  - **students.py**: Student management routes
  - **sessions.py**: Session tracking routes  
  - **schools.py**: School management routes
  - **api.py**: API endpoints
  - **admin.py**: Administrative functions
  - **dashboard.py**: Main dashboard views

### Database Schema

The application uses SQLite with the following main entities:
- **Students**: Core student information with demographics
- **Goals**: Therapy goals linked to students
- **Objectives**: Specific measurable objectives under goals
- **Sessions**: Individual therapy sessions
- **TrialLog**: Trial data tracking objective progress
- **SOAPNotes**: Subjective, Objective, Assessment, Plan notes
- **Schools**: School information and scheduling

### Key Relationships

- Students have multiple Goals
- Goals have multiple Objectives  
- Sessions belong to Students
- TrialLogs track progress on Objectives within Sessions
- SOAPNotes are created for Sessions

### File Organization

- **templates/**: Jinja2 HTML templates for all views
- **static/**: CSS, JavaScript, and other static assets
- **data/**: SQLite database storage location

## Development Notes

### Database Connections

The application uses context managers for database connections via `get_db_connection()` in database.py. All database operations should use this pattern for proper connection handling.

### Model Usage

Models inherit from BaseModel which provides:
- `get_by_id()`: Retrieve single record by ID
- `from_row()`: Convert SQLite row to model instance
- `to_dict()`: Convert model to dictionary
- Automatic filtering of constructor parameters from joined queries

### Session Management

The application tracks detailed trial data with support levels:
- Independent
- Minimal Support  
- Moderate Support
- Maximal Support
- Incorrect

Progress calculations are built into the Objective model to track accuracy percentages.

## Implementation Log Protocol

**CRITICAL WORKFLOW INSTRUCTIONS:**

### For Significant Changes/Implementations:
- ALWAYS create or update an IMPLEMENTATION_LOG.md file documenting:
  - Original requirements/requests  
  - Complete implementation details
  - Files modified and changes made
  - Technical enhancements added
  - Testing recommendations
  - Date and scope of work

### At START of Each New Session:
1. **IMMEDIATELY check for and read the most recent IMPLEMENTATION_LOG.md**
2. Review recent changes and current project state
3. Reference this context when working on new tasks
4. Ask user if they want to discuss recent changes or if new work should build upon them

### Implementation Log Location:
- Always save as `IMPLEMENTATION_LOG.md` in project root
- If multiple logs needed, use date-based naming: `IMPLEMENTATION_LOG_2025-08-21.md`

This ensures project continuity and context preservation across all sessions.