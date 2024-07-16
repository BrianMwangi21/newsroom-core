import click
from flask import current_app as app

from .cli import newsroom_cli


@newsroom_cli.cli.command("elastic_reindex")
@click.option("-r", "--resource", required=True, help="Resource to reindex")
@click.option("-s", "--requests-per-second", default=1000, type=int, help="Number of requests per second")
def elastic_reindex(resource, requests_per_second=1000):
    assert resource in ("items", "agenda", "history")
    return app.data.elastic.reindex(resource, requests_per_second=requests_per_second)
