#!/usr/bin/env python3
"""
SQL Terminal — an interactive SQLite shell with rich, formatted table output.

Run:
    python main.py

Type SQL statements at the sql> prompt (end each statement with a semicolon).
Special commands:
    .tables             list all tables
    .schema <table>      show a table's columns/types
    .reset               drop and reseed the demo data
    .help                show help
    .exit / .quit        leave the shell
"""

import sqlite3

from database import get_connection, init_demo_data, reset_demo_data
from display import (
    console,
    show_results,
    show_message,
    show_error,
    show_tables,
    show_schema,
)

HELP_TEXT = """
[bold cyan]Example SQL you can run[/bold cyan]
  SELECT * FROM Sports;
  SELECT Name FROM Sports WHERE Favorite_Sport = 'Cricket';
  INSERT INTO Sports (Name, Favorite_Sport) VALUES ('Ali', 'Football');
  UPDATE Sports SET Favorite_Sport = 'Tennis' WHERE Name = 'Sara';
  DELETE FROM Sports WHERE Name = 'Bilal';
  SELECT Students.Name, Grades.Subject, Grades.Score
    FROM Students JOIN Grades ON Students.Name = Grades.Student_Name
    WHERE Grades.Score > 80;

[bold cyan]Meta commands[/bold cyan]
  .tables               list all tables
  .schema <table>        show columns for a table
  .reset                 drop & reseed demo data
  .help                  show this help message
  .exit / .quit          exit the shell
"""


def handle_meta_command(command, conn):
    """Handle a leading-dot meta command. Returns False if the shell should exit."""
    parts = command.strip().split()
    cmd = parts[0].lower()

    if cmd in (".exit", ".quit"):
        return False

    if cmd == ".help":
        console.print(HELP_TEXT)
        return True

    if cmd == ".tables":
        cur = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        names = [row[0] for row in cur.fetchall()]
        show_tables(names)
        return True

    if cmd == ".schema":
        if len(parts) < 2:
            show_error("Usage: .schema <table_name>")
            return True
        table_name = parts[1]
        cur = conn.execute(f"PRAGMA table_info({table_name});")
        info = cur.fetchall()
        if not info:
            show_error(f"No such table: {table_name}")
        else:
            show_schema(table_name, info)
        return True

    if cmd == ".reset":
        reset_demo_data(conn)
        show_message("Demo data reset.")
        return True

    show_error(f"Unknown command: {command}")
    return True


def run_sql(sql, conn):
    """Execute one SQL statement and print a rich table or a status message."""
    try:
        cur = conn.cursor()
        cur.execute(sql)

        if cur.description is not None:
            # SELECT-style statement -> has columns to show
            columns = [d[0] for d in cur.description]
            rows = cur.fetchall()
            show_results(columns, rows)
        else:
            # INSERT / UPDATE / DELETE / CREATE etc.
            conn.commit()
            affected = cur.rowcount if cur.rowcount != -1 else 0
            show_message(f"OK — {affected} row(s) affected.")

    except sqlite3.Error as e:
        show_error(str(e))


def main():
    conn = get_connection()
    init_demo_data(conn)

    console.print(
        "[bold green]SQL Terminal[/bold green] — demo SQLite database loaded "
        "(tables: [cyan]Sports[/cyan], [cyan]Students[/cyan], [cyan]Grades[/cyan]).\n"
        "Type [bold].help[/bold] for examples, [bold].exit[/bold] to quit.\n"
    )

    buffer = ""
    while True:
        try:
            prompt = "sql> " if not buffer else "...> "
            line = console.input(f"[bold blue]{prompt}[/bold blue]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        stripped = line.strip()

        if not stripped and not buffer:
            continue

        # Meta commands only count at the start of a fresh statement
        if stripped.startswith(".") and not buffer:
            if not handle_meta_command(stripped, conn):
                console.print("[yellow]Goodbye![/yellow]")
                break
            continue

        buffer += (" " if buffer else "") + line

        # A statement is considered complete once it ends with a semicolon
        if buffer.rstrip().endswith(";"):
            run_sql(buffer.strip(), conn)
            buffer = ""

    conn.close()


if __name__ == "__main__":
    main()