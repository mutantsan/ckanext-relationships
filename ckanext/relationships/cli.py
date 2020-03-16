# -*- coding: utf-8 -*-

import click


@click.group()
def relationship():
    pass


@relationship.command()
def init():
    from .models import create_tables

    click.echo("Creating database package relationships tables...")
    create_tables()
    click.secho("Done.", fg="green")