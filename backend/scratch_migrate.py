import sqlite3

db_path = 'd:/MedLens/backend/medlens_history.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

columns_to_add = [
    "blood_group VARCHAR",
    "allergies TEXT",
    "conditions TEXT",
    "current_meds TEXT",
    "emergency_contact VARCHAR"
]

for col in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col}")
        print(f"Added column {col}")
    except sqlite3.OperationalError as e:
        print(f"Column {col} might already exist or error: {e}")

conn.commit()
conn.close()
print("Migration completed.")
