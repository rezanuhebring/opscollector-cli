"""Internal CLI helpers: table rendering and error handling."""

from __future__ import annotations

from typing import Any, Sequence

from rich.console import Console
from rich.table import Table

from app.core.exceptions import OpsCollectorError

console = Console()


def render_table(title: str, columns: list[str], rows: Sequence[Sequence[Any]]) -> None:
    table = Table(title=title, show_lines=False, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    for r in rows:
        table.add_row(*[str(c) if c is not None else "" for c in r])
    console.print(table)


def render_dict(title: str, data: dict[str, Any]) -> None:
    table = Table(title=title, show_header=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    for k, v in data.items():
        table.add_row(str(k), str(v) if v is not None else "")
    console.print(table)


def success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def info(message: str) -> None:
    console.print(f"[cyan]{message}[/cyan]")


def warn(message: str) -> None:
    console.print(f"[yellow]! {message}[/yellow]")


def handle_error(func):
    """Decorator that catches application errors and prints a friendly message."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OpsCollectorError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise SystemExit(1)

    return wrapper
