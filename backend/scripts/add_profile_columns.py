import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "dailyplanner.db")

def migrate():
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add columns
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN username VARCHAR(255)")
        print("Added username column.")
    except Exception as e:
        print("Username column might already exist:", e)

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN dob VARCHAR(50)")
        print("Added dob column.")
    except Exception as e:
        print("DOB column might already exist:", e)

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN gender VARCHAR(50)")
        print("Added gender column.")
    except Exception as e:
        print("Gender column might already exist:", e)

    try:
        cursor.execute("CREATE UNIQUE INDEX ix_user_profiles_username ON user_profiles(username) WHERE username IS NOT NULL")
        print("Added unique index for username.")
    except Exception as e:
        print("Index might already exist:", e)

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
