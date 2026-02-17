"""Batou operational maintenance and migration tooling."""

import typer

from batou.check import check
from batou.migrate_toml import migrate
from batou.toml_to_ini import convert

app = typer.Typer(
    no_args_is_help=True,
    help="Batou operational maintenance and migration tooling.",
)

app.command(name="check")(check)
app.command(name="migrate-toml")(migrate)
app.command(name="toml-to-ini")(convert)
