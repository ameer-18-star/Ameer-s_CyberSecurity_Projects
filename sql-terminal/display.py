"""
display.py
Formats SQL results as terminal tables using the `rich` library.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def show_results(columns, rows, title="Query Result"):
    """Render SELECT results as a rich table."""
    if not rows:
        console.print(Panel("[yellow]0 rows returned[/yellow]", title=title, expand=False))
        return

    table = Table(title=title, header_style="bold cyan", show_lines=False)
    for col in columns:
        table.add_column(str(col), overflow="fold")

    for row in rows:
        table.add_row(*[("" if v is None else str(v)) for v in row])

    console.print(table)
    console.print(f"[dim]{len(rows)} row(s) returned[/dim]")


def show_message(message, style="green"):
    console.print(f"[{style}]{message}[/{style}]")


def show_error(message):
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_tables(table_names):
    if not table_names:
        show_message("No tables found.", style="yellow")
        return
    table = Table(title="Tables in Database", header_style="bold cyan")
    table.add_column("Table Name")
    for name in table_names:
        table.add_row(name)
    console.print(table)


def show_schema(table_name, columns_info):
    """columns_info is the row set returned by PRAGMA table_info(<table>)."""
    table = Table(title=f"Schema: {table_name}", header_style="bold cyan")
    table.add_column("Column")
    table.add_column("Type")
    table.add_column("Not Null")
    table.add_column("Default")
    table.add_column("Primary Key")
    for col in columns_info:
        cid, name, ctype, notnull, dflt, pk = col
        table.add_row(
            name,
            ctype,
            "Yes" if notnull else "No",
            str(dflt) if dflt is not None else "",
            "Yes" if pk else "No",
        )
    console.print(table)