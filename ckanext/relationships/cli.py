# -*- coding: utf-8 -*-

import click


@click.group()
def relationship():
    pass


@relationship.command()
def init():
    from .model import create_tables

    click.echo("Creating package relationships database tables...")
    create_tables()
    click.secho("Done.", fg="green")


@relationship.command()
def drop():
    from .model import drop_tables

    if click.confirm(
        'Are you sure you want to drop all tables?',
            abort=False):
        drop_tables()
        click.secho("Done.", fg="green")
    else:
        click.echo("[INFO] GITIGNORE was not generated.", fg='blue')


def get_commands():
    return [relationship]
