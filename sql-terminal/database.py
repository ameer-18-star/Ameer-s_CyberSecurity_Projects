"""
database.py
Creates the demo SQLite database and seeds it with sample data.

Tables:
    Sports    -> Name, Favorite_Sport             (matches the DBMS/SQL notes)
    Students  -> Name, Age, Class                  (27 students, for JOIN practice)
    Grades    -> Student_Name, Subject, Score       (two subjects per student)
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "demo.db"


def get_connection():
    """Create (or reuse) the SQLite database file and return a connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Demo data — 27 students, each with an age, class, favorite sport, and
# scores in two subjects, so joins across all three tables return real,
# varied results instead of a handful of rows.
# ---------------------------------------------------------------------------

STUDENTS = [
    # (Name, Age, Class)
    ("Ali", 14, "9-A"),
    ("Hina", 14, "9-A"),
    ("Zain", 15, "9-B"),
    ("Sara", 15, "9-B"),
    ("Bilal", 15, "10-A"),
    ("Ayesha", 15, "10-A"),
    ("Usman", 16, "10-B"),
    ("Fatima", 16, "10-B"),
    ("Hamza", 16, "11-A"),
    ("Mariam", 16, "11-A"),
    ("Ahmed", 17, "11-B"),
    ("Sana", 17, "11-B"),
    ("Adeel", 17, "12-A"),
    ("Nida", 17, "12-A"),
    ("Kashif", 18, "12-B"),
    ("Rabia", 18, "12-B"),
    ("Faisal", 14, "9-A"),
    ("Iqra", 14, "9-B"),
    ("Tariq", 15, "10-A"),
    ("Zainab", 15, "10-B"),
    ("Omar", 16, "11-A"),
    ("Hira", 16, "11-B"),
    ("Salman", 17, "12-A"),
    ("Amna", 17, "12-B"),
    ("Junaid", 18, "12-B"),
    ("Mahnoor", 14, "9-A"),
    ("Waqas", 15, "10-A"),
]

# Cycled across students so every sport shows up multiple times
SPORTS_CYCLE = [
    "Cricket", "Football", "Badminton", "Hockey", "Tennis",
    "Volleyball", "Basketball", "Table Tennis", "Swimming", "Chess",
]

SPORTS = [
    (name, SPORTS_CYCLE[i % len(SPORTS_CYCLE)])
    for i, (name, _age, _cls) in enumerate(STUDENTS)
]

# Two subjects per student, with varied scores (Student_Name, Subject, Score)
SUBJECT_PAIRS = [
    ("Computer Science", "Math"),
    ("Physics", "English"),
]

_SCORE_SEED = [88, 76, 92, 81, 70, 95, 84, 67, 73, 99, 58, 85, 90, 62, 78]

GRADES = []
for i, (name, _age, _cls) in enumerate(STUDENTS):
    subj_a, subj_b = SUBJECT_PAIRS[i % 2]
    score_a = _SCORE_SEED[i % len(_SCORE_SEED)]
    score_b = _SCORE_SEED[(i + 5) % len(_SCORE_SEED)]
    GRADES.append((name, subj_a, score_a))
    GRADES.append((name, subj_b, score_b))


def init_demo_data(conn):
    """Create tables if they don't exist and seed them once with demo rows."""
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS Sports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Favorite_Sport TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Age INTEGER,
            Class TEXT
        );

        CREATE TABLE IF NOT EXISTS Grades (
            grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Student_Name TEXT NOT NULL,
            Subject TEXT NOT NULL,
            Score INTEGER
        );
        """
    )

    # Only seed if the table is empty, so re-running the app doesn't duplicate rows
    cur.execute("SELECT COUNT(*) FROM Sports")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO Sports (Name, Favorite_Sport) VALUES (?, ?)", SPORTS
        )

    cur.execute("SELECT COUNT(*) FROM Students")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO Students (Name, Age, Class) VALUES (?, ?, ?)", STUDENTS
        )

    cur.execute("SELECT COUNT(*) FROM Grades")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO Grades (Student_Name, Subject, Score) VALUES (?, ?, ?)",
            GRADES,
        )

    conn.commit()


def reset_demo_data(conn):
    """Drop and recreate all demo tables with fresh seed data (used by .reset)."""
    conn.executescript(
        """
        DROP TABLE IF EXISTS Sports;
        DROP TABLE IF EXISTS Students;
        DROP TABLE IF EXISTS Grades;
        """
    )
    conn.commit()
    init_demo_data(conn)