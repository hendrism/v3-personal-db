# School System Feature Archive

This directory contains the school scheduling system that was removed from the main application for simplification.

## What's Included

- `school.py` - School and StudentSchedule models with Thomas Stone High School scheduling
- `schools.py` - Flask routes for school management
- `school*.html` - Templates for school forms and details
- `schools.html` - School listing template

## Features Implemented

- School information management (name, address, contact info)
- Thomas Stone High School bell schedule with extensions
- Student class schedules with lunch periods
- JSON-based class/room tracking
- Schedule extensions (regular, 1st period, 2nd period, early dismissal)

## Database Tables

The school system requires these tables:

```sql
CREATE TABLE schools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    fax TEXT,
    hours TEXT,
    schedule_type TEXT DEFAULT 'simple',
    current_extension TEXT DEFAULT 'regular',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    school_id INTEGER NOT NULL,
    lunch_type TEXT DEFAULT 'A',
    classes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students (id),
    FOREIGN KEY (school_id) REFERENCES schools (id)
);
```

## To Re-implement

1. Copy files back to their original locations
2. Add school imports to `models/__init__.py`
3. Register schools blueprint in `app.py`
4. Add table creation calls to `database.py`
5. Update navigation templates to include school links

## Removed on

Date: August 22, 2025
Reason: Overly complex for minimal usage, cluttering core session tracking workflow