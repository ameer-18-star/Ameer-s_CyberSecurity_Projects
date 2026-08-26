# SQL Command Reference — SQL Terminal Demo Database

All examples below use the three demo tables and can be typed straight into
`sql>` (remember the trailing `;`). Schema recap:

| Table    | Columns                                    |
|----------|---------------------------------------------|
| Sports   | id, Name, Favorite_Sport                     |
| Students | student_id, Name, Age, Class                 |
| Grades   | grade_id, Student_Name, Subject, Score        |

---

## 1. Viewing data (SELECT)

```sql
-- Everything in a table
SELECT * FROM Sports;

-- Specific columns only
SELECT Name, Favorite_Sport FROM Sports;

-- Unique values only (no duplicates)
SELECT DISTINCT Favorite_Sport FROM Sports;

-- Unique class list
SELECT DISTINCT Class FROM Students;

-- Count how many rows a table has
SELECT COUNT(*) FROM Students;

-- Rename a column in the output
SELECT Name AS Student_Name, Age AS Student_Age FROM Students;
```

---

## 2. Filtering rows (WHERE)

```sql
-- Exact match
SELECT Name FROM Sports WHERE Favorite_Sport = 'Cricket';

-- Not equal
SELECT Name FROM Sports WHERE Favorite_Sport != 'Cricket';

-- Numeric comparison
SELECT * FROM Students WHERE Age > 16;
SELECT * FROM Students WHERE Age >= 16 AND Age <= 17;

-- Range shortcut
SELECT * FROM Students WHERE Age BETWEEN 16 AND 17;

-- Multiple allowed values
SELECT * FROM Students WHERE Class IN ('9-A', '9-B');

-- Combine conditions
SELECT * FROM Students WHERE Age > 15 AND Class LIKE '1%';

-- Either condition
SELECT * FROM Sports WHERE Favorite_Sport = 'Cricket' OR Favorite_Sport = 'Football';

-- Pattern matching (LIKE) — % is a wildcard for "anything"
SELECT * FROM Students WHERE Name LIKE 'A%';       -- starts with A
SELECT * FROM Students WHERE Name LIKE '%a';        -- ends with a
SELECT * FROM Students WHERE Class LIKE '12-%';     -- any 12th-grade class

-- NULL checks (no NULLs exist in the demo data, but this is the syntax)
SELECT * FROM Grades WHERE Score IS NULL;
SELECT * FROM Grades WHERE Score IS NOT NULL;
```

---

## 3. Sorting and limiting results

```sql
-- Alphabetical
SELECT * FROM Students ORDER BY Name ASC;

-- Highest scores first
SELECT * FROM Grades ORDER BY Score DESC;

-- Sort by one column, break ties with another
SELECT * FROM Students ORDER BY Class ASC, Age DESC;

-- Top 5 highest scores only
SELECT * FROM Grades ORDER BY Score DESC LIMIT 5;

-- "Page 2" of results (skip first 10, take next 10)
SELECT * FROM Students ORDER BY Name LIMIT 10 OFFSET 10;
```

---

## 4. Aggregating data (COUNT, AVG, SUM, MIN, MAX, GROUP BY)

```sql
-- Average score across everyone
SELECT AVG(Score) FROM Grades;

-- Highest and lowest score
SELECT MAX(Score) AS Highest, MIN(Score) AS Lowest FROM Grades;

-- How many students play each sport
SELECT Favorite_Sport, COUNT(*) AS Total
FROM Sports
GROUP BY Favorite_Sport;

-- Average score per subject
SELECT Subject, AVG(Score) AS Avg_Score
FROM Grades
GROUP BY Subject;

-- Students per class
SELECT Class, COUNT(*) AS Student_Count
FROM Students
GROUP BY Class
ORDER BY Student_Count DESC;

-- Only show subjects where the average score is above 80
SELECT Subject, AVG(Score) AS Avg_Score
FROM Grades
GROUP BY Subject
HAVING AVG(Score) > 80;

-- Highest score per student
SELECT Student_Name, MAX(Score) AS Best_Score
FROM Grades
GROUP BY Student_Name;
```

---

## 5. Combining tables (JOIN)

```sql
-- Each student with their favorite sport
SELECT Students.Name, Students.Class, Sports.Favorite_Sport
FROM Students
JOIN Sports ON Students.Name = Sports.Name;

-- Each student with all their grades
SELECT Students.Name, Grades.Subject, Grades.Score
FROM Students
JOIN Grades ON Students.Name = Grades.Student_Name;

-- Only students who scored above 90
SELECT Students.Name, Grades.Subject, Grades.Score
FROM Students
JOIN Grades ON Students.Name = Grades.Student_Name
WHERE Grades.Score > 90;

-- All three tables together
SELECT Students.Name, Students.Class, Sports.Favorite_Sport,
       Grades.Subject, Grades.Score
FROM Students
JOIN Sports ON Students.Name = Sports.Name
JOIN Grades ON Students.Name = Grades.Student_Name
ORDER BY Grades.Score DESC;

-- LEFT JOIN: keep every student even if they have no matching sport/grade row
SELECT Students.Name, Sports.Favorite_Sport
FROM Students
LEFT JOIN Sports ON Students.Name = Sports.Name;

-- Cricket fans and their grades
SELECT Sports.Name, Sports.Favorite_Sport, Grades.Subject, Grades.Score
FROM Sports
JOIN Grades ON Sports.Name = Grades.Student_Name
WHERE Sports.Favorite_Sport = 'Cricket';
```

---

## 6. Modifying data (INSERT, UPDATE, DELETE)

```sql
-- Add a new student
INSERT INTO Students (Name, Age, Class) VALUES ('Noor', 15, '10-A');

-- Add their sport and a grade too
INSERT INTO Sports (Name, Favorite_Sport) VALUES ('Noor', 'Cricket');
INSERT INTO Grades (Student_Name, Subject, Score) VALUES ('Noor', 'Math', 91);

-- Insert several rows at once
INSERT INTO Sports (Name, Favorite_Sport) VALUES
    ('Bilal', 'Football'),
    ('Sara', 'Chess');

-- Update a value
UPDATE Sports SET Favorite_Sport = 'Tennis' WHERE Name = 'Sara';

-- Update multiple columns at once
UPDATE Students SET Age = 16, Class = '10-B' WHERE Name = 'Ali';

-- Bump every score in a subject by 5 (capped scenario, careful with WHERE!)
UPDATE Grades SET Score = Score + 5 WHERE Subject = 'Math';

-- Delete a specific row
DELETE FROM Sports WHERE Name = 'Bilal';

-- Delete rows matching a condition
DELETE FROM Grades WHERE Score < 60;

-- Delete everything in a table (keeps the table structure)
DELETE FROM Grades;
```

---

## 7. Changing table structure (CREATE, ALTER, DROP)

```sql
-- Create a brand-new table
CREATE TABLE Attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Student_Name TEXT NOT NULL,
    Date TEXT NOT NULL,
    Present INTEGER  -- 1 = present, 0 = absent
);

-- Add a column to an existing table
ALTER TABLE Students ADD COLUMN Email TEXT;

-- Rename a table
ALTER TABLE Attendance RENAME TO DailyAttendance;

-- Remove a table entirely
DROP TABLE IF EXISTS DailyAttendance;
```

---

## 8. Useful one-off scenarios

```sql
-- "Which students play Cricket AND scored over 85?"
SELECT DISTINCT Students.Name
FROM Students
JOIN Sports ON Students.Name = Sports.Name
JOIN Grades ON Students.Name = Grades.Student_Name
WHERE Sports.Favorite_Sport = 'Cricket' AND Grades.Score > 85;

-- "What's the class-wide average score, per class?"
SELECT Students.Class, AVG(Grades.Score) AS Class_Avg
FROM Students
JOIN Grades ON Students.Name = Grades.Student_Name
GROUP BY Students.Class
ORDER BY Class_Avg DESC;

-- "Top scorer in each subject" (subquery)
SELECT Subject, Student_Name, Score
FROM Grades g1
WHERE Score = (SELECT MAX(Score) FROM Grades g2 WHERE g2.Subject = g1.Subject);

-- "Students who do NOT have a grade recorded" (anti-join)
SELECT Students.Name
FROM Students
LEFT JOIN Grades ON Students.Name = Grades.Student_Name
WHERE Grades.grade_id IS NULL;

-- Conditional labeling with CASE
SELECT Student_Name, Subject, Score,
    CASE
        WHEN Score >= 90 THEN 'A'
        WHEN Score >= 80 THEN 'B'
        WHEN Score >= 70 THEN 'C'
        ELSE 'Needs Improvement'
    END AS Grade_Letter
FROM Grades;

-- Combine two result sets into one list (UNION removes duplicates)
SELECT Name FROM Students
UNION
SELECT Name FROM Sports;
```

---

## 9. Shell meta commands (not SQL, but built into this project)

| Command           | What it does                       |
|--------------------|--------------------------------------|
| `.tables`          | list all tables                       |
| `.schema Students` | show a table's columns and types      |
| `.reset`           | drop and reseed the demo data         |
| `.help`            | show quick examples                    |
| `.exit` / `.quit`  | leave the shell                        |

---

### Tip
Anything valid in SQLite works here — this list covers the common day-to-day
patterns, but you can also try window functions (`ROW_NUMBER() OVER (...)`),
`EXISTS`, correlated subqueries, and more if you want to go further.