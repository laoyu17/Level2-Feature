from __future__ import annotations

import typer

from l2_features.cli.commands.benchmark import benchmark_command
from l2_features.cli.commands.compute import compute_entry
from l2_features.cli.commands.replay import replay_command
from l2_features.cli.commands.ui import ui_command
from l2_features.cli.commands.validate_schema import validate_schema_command

app = typer.Typer(help="Level2 feature extraction toolkit")

app.command("compute")(compute_entry)
app.command("replay")(replay_command)
app.command("benchmark")(benchmark_command)
app.command("validate-schema")(validate_schema_command)
app.command("ui")(ui_command)


if __name__ == "__main__":
    app()
