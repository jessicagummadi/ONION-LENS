import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import sqlite3
from backend.app.database import init_db

def migrate():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute('PRAGMA table_info(inspections)')
    cols = [r[1] for r in c.fetchall()]

    new_cols = [
        ('inspector_id', 'TEXT DEFAULT "INSP-APMC-8492"'),
        ('total_onions', 'INTEGER DEFAULT 0'),
        ('healthy_onions', 'INTEGER DEFAULT 0'),
        ('defective_onions', 'INTEGER DEFAULT 0'),
        ('image_path', 'TEXT'),
        ('created_at', 'DATETIME')
    ]

    for col_name, col_type in new_cols:
        if col_name not in cols:
            c.execute(f"ALTER TABLE inspections ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")

    conn.commit()
    conn.close()

    init_db()
    print("Database migration & table initialization completed successfully!")

if __name__ == "__main__":
    migrate()
