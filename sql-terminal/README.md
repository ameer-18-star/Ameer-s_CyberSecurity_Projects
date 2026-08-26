# SQL Terminal

A small Python project that gives you a real SQL-like database (SQLite) and an
interactive terminal shell: type SQL, hit enter, get a nicely formatted table
back — no external database server required.

## How it works

- **Database engine:** Python's built-in `sqlite3` module (a real DBMS, just
  file-based — no separate server to install, like MySQL would need).
- **Table output:** the [`rich`](https://github.com/Textualize/rich) library
  renders query results as boxed terminal tables.
- **Demo data:** three pre-loaded tables so you have something to query
  immediately.

## Project structure

```
sql-terminal/
├── main.py          # entry point — the interactive SQL shell
├── database.py       # creates demo.db and seeds demo tables
├── display.py         # formats results as rich tables
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

On first run this creates `demo.db` in the project folder and seeds it with
demo data. Re-running the app reuses the same file and won't duplicate rows.

## Demo tables

**Sports** (Name, Favorite_Sport) — matches the example from the DBMS/SQL notes:

| id | Name   | Favorite_Sport |
|----|--------|----------------|
| 1  | Ali    | Cricket        |
| 2  | Hina   | Football       |
| 3  | Zain   | Cricket        |
| 4  | Sara   | Badminton      |
| 5  | Bilal  | Hockey         |
| 6  | Ayesha | Cricket        |

**Students** (Name, Age, Class) and **Grades** (Student_Name, Subject, Score)
are included too, so you can practice `JOIN` queries across tables.

## Example commands to try

```sql
SELECT * FROM Sports;

SELECT Name FROM Sports WHERE Favorite_Sport = 'Cricket';

INSERT INTO Sports (Name, Favorite_Sport) VALUES ('Ali', 'Football');

UPDATE Sports SET Favorite_Sport = 'Tennis' WHERE Name = 'Sara';

DELETE FROM Sports WHERE Name = 'Bilal';

SELECT Students.Name, Grades.Subject, Grades.Score
FROM Students
JOIN Grades ON Students.Name = Grades.Student_Name
WHERE Grades.Score > 80;
```

Every statement must end with a semicolon `;` — you can even split a long
query across multiple lines, and the shell will wait until it sees the `;`
before running it.

## Meta commands

| Command          | What it does                          |
|------------------|----------------------------------------|
| `.tables`        | list all tables in the database        |
| `.schema <table>`| show a table's columns and types       |
| `.reset`         | drop and reseed the demo data          |
| `.help`          | show example queries and commands      |
| `.exit` / `.quit`| leave the shell                        |

## Extending it

- Add your own tables by editing `database.py`.
- This is plain SQLite, so any valid SQLite syntax works — `GROUP BY`,
  `ORDER BY`, aggregate functions (`COUNT`, `AVG`, `SUM`), subqueries, etc.
- To inspect `demo.db` outside this app, any SQLite browser (e.g. "DB Browser
  for SQLite") or the `sqlite3` CLI will open it directly.