import sqlite3

conn = sqlite3.connect('planner.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE template_tasks ADD COLUMN requires_reason BOOLEAN DEFAULT 0;')
    print('Added requires_reason')
except Exception as e:
    print('requires_reason error:', e)

try:
    cursor.execute('ALTER TABLE template_tasks ADD COLUMN allows_alternate BOOLEAN DEFAULT 0;')
    print('Added allows_alternate')
except Exception as e:
    print('allows_alternate error:', e)

conn.commit()
conn.close()
