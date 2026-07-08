"""CLI: database maintenance commands (seed demo data, etc.)."""

from __future__ import annotations

import typer

from app.cli._console import console, success
from app.database.seed import force_seed_demo_data, seed_demo_data
from app.database.db import init_db
from app.database.seed import seed_reference_data

app = typer.Typer(help="Database maintenance", no_args_is_help=True)


@app.command("seed-demo")
def seed_demo_cmd(
    force: bool = typer.Option(False, "--force", help="Seed even if data exists"),
) -> None:
    """Load example data so the dashboard and lists are populated.

    By default this is a no-op if you already have incidents/BAU. Use --force
    to always add the demo set (useful for trying out the app).
    """
    if force:
        added = force_seed_demo_data()
        success(f"Demo data added ({added} incidents inserted)")
    else:
        seed_demo_data()
        success("Demo data ready (skipped because operational data already exists)")
