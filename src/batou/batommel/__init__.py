"""Batou operational maintenance and migration tooling."""

import typer

from batou.batommel.deploy import deploy
from batou.check import check
from batou.ini_to_toml import migrate
from batou.toml_to_ini import convert

app = typer.Typer(
    no_args_is_help=True,
    help="Batou operational maintenance and migration tooling.",
)

app.command(name="check")(check)
app.command(name="ini-to-toml")(migrate)
app.command(name="toml-to-ini")(convert)
app.command(name="deploy")(deploy)
