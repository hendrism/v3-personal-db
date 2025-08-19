#!/usr/bin/env python3
"""
V3 Enhancement Setup Script
Run this to upgrade your existing v3 system with objectives support

Usage:
    python setup_objectives.py
"""

import os
import sqlite3
from datetime import datetime

def backup_database():
    """Create a backup of the existing database."""
    if os.path.exists('data/students.db'):
        backup_name = f"data/students_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.system(f"cp data/students.db {backup_name}")
        print(f"✅ Database backed up to {backup_name}")
        return True
    return False

def check_existing_database():
    """Check if we have an existing v3 database."""
    if not os.path.exists('data/students.db'):
        print("❌ No existing database found. This script is for upgrading existing v3 systems.")
        return False
    
    # Check if objectives table already exists
    conn = sqlite3.connect('data/students.db')
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='objectives'")
    exists = cursor.fetchone() is not None
    conn.close()
    
    if exists:
        print("✅ Objectives table already exists!")
        return True
    else:
        print("📦 Found existing v3 database without objectives. Ready to upgrade.")
        return True

def upgrade_database():
    """Add objectives table and update trial_logs table."""
    conn = sqlite3.connect('data/students.db')
    
    try:
        print("🔧 Adding objectives table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS objectives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                target_percentage INTEGER DEFAULT 80,
                notes TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals (id)
            )
        ''')
        
        print("🔧 Updating trial_logs table...")
        # Check if objective_id column exists
        cursor = conn.execute("PRAGMA table_info(trial_logs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'objective_id' not in columns:
            conn.execute('ALTER TABLE trial_logs ADD COLUMN objective_id INTEGER')
            print("   Added objective_id column to trial_logs")
        
        print("🔧 Creating indexes...")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_objectives_goal ON objectives(goal_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trials_objective ON trial_logs(objective_id)')
        
        conn.commit()
        print("✅ Database upgrade completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error upgrading database: {e}")
        return False
    finally:
        conn.close()
    
    return True

def add_sample_objectives():
    """Add sample objectives to existing goals."""
    conn = sqlite3.connect('data/students.db')
    
    try:
        # Get existing goals
        cursor = conn.execute('SELECT id, description FROM goals WHERE active = 1')
        goals = cursor.fetchall()
        
        if not goals:
            print("ℹ️  No existing goals found. Skipping sample objectives.")
            return True
        
        print(f"🔧 Adding sample objectives to {len(goals)} existing goals...")
        
        for goal_id, goal_desc in goals:
            # Check if this goal already has objectives
            cursor = conn.execute('SELECT COUNT(*) FROM objectives WHERE goal_id = ?', (goal_id,))
            if cursor.fetchone()[0] > 0:
                continue  # Skip if already has objectives
            
            # Add sample objectives based on goal description
            if '/r/' in goal_desc.lower() or 'articulation' in goal_desc.lower():
                objectives = [
                    f"Produce target sound in initial position with 85% accuracy",
                    f"Produce target sound in medial position with 85% accuracy", 
                    f"Produce target sound in final position with 85% accuracy",
                    f"Use target sound in connected speech with 80% accuracy"
                ]
            elif 'vocabulary' in goal_desc.lower():
                objectives = [
                    f"Define new vocabulary words with 80% accuracy",
                    f"Use new vocabulary in sentences with 75% accuracy",
                    f"Answer comprehension questions about vocabulary with 85% accuracy"
                ]
            else:
                # Generic objectives
                objectives = [
                    f"Complete target tasks with minimal support (80% accuracy)",
                    f"Demonstrate skill in structured activities (85% accuracy)",
                    f"Apply skill in functional contexts (75% accuracy)"
                ]
            
            for obj_desc in objectives:
                conn.execute('''
                    INSERT INTO objectives (goal_id, description, target_percentage)
                    VALUES (?, ?, ?)
                ''', (goal_id, obj_desc, 80))
        
        conn.commit()
        print("✅ Sample objectives added!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error adding sample objectives: {e}")
        return False
    finally:
        conn.close()
    
    return True

def verify_upgrade():
    """Verify the upgrade was successful."""
    conn = sqlite3.connect('data/students.db')
    
    try:
        # Check objectives table
        cursor = conn.execute('SELECT COUNT(*) FROM objectives')
        obj_count = cursor.fetchone()[0]
        
        # Check trial_logs has objective_id column
        cursor = conn.execute("PRAGMA table_info(trial_logs)")
        columns = [row[1] for row in cursor.fetchall()]
        has_objective_id = 'objective_id' in columns
        
        print(f"\n📊 Upgrade Verification:")
        print(f"   • Objectives table: ✅ ({obj_count} objectives)")
        print(f"   • Trial logs updated: {'✅' if has_objective_id else '❌'}")
        
        return obj_count >= 0 and has_objective_id
        
    except Exception as e:
        print(f"❌ Error verifying upgrade: {e}")
        return False
    finally:
        conn.close()

def main():
    print("🚀 V3 Enhancement Setup - Adding Objectives Support")
    print("=" * 50)
    
    # Step 1: Check existing system
    if not check_existing_database():
        return
    
    # Step 2: Backup
    backup_database()
    
    # Step 3: Upgrade database
    if not upgrade_database():
        print("❌ Database upgrade failed. Check the backup and try again.")
        return
    
    # Step 4: Add sample data
    add_sample_objectives()
    
    # Step 5: Verify
    if verify_upgrade():
        print("\n🎉 SUCCESS! Your v3 system has been enhanced with objectives support!")
        print("\nNext steps:")
        print("1. Replace your existing files with the enhanced versions:")
        print("   - database.py")
        print("   - models.py") 
        print("   - app.py")
        print("   - templates/session_detail.html")
        print("   - Add templates/objective_form.html")
        print("   - Add templates/goal_form.html")
        print("   - Update templates/student_detail.html")
        print("\n2. Restart your Flask app: python app.py")
        print("3. Visit a student page to see goals/objectives")
        print("4. Try the enhanced session tracking!")
    else:
        print("❌ Verification failed. Check the error messages above.")

if __name__ == "__main__":
    main()