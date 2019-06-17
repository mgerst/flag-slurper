import click
from terminaltables import AsciiTable

from .autolib.models import database_proxy, SSHKey, Service
from .project import Project
from . import utils


@click.group()
@click.pass_context
def keys(ctx):
    """
    View and manage shared ssh keys for use with autopwn.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error('SSH Key commands require an active project')
        exit(4)
    p.connect_database()
    ctx.obj = p


@keys.command()
@click.option('-n', '--name', type=click.STRING, help='Filter by key name', default=None)
def ls(name):
    """
    List all keys used by autopwn.
    """
    with database_proxy.obj:
        keys = SSHKey.select()

        if name:
            keys = keys.where(SSHKey.name.contains(name))

        if keys.count() == 0:
            utils.report_warning('No keys found')
            exit(1)

        data = [[k.id, k.name, 'Y' if k.active else 'N'] for k in keys]
        data.insert(0, ['ID', 'Name', 'Active?'])
        table = AsciiTable(data)
        utils.conditional_page(table.table, len(data))


@keys.command()
@click.argument('id', metavar='ID', type=click.INT)
def show(id):
    """
    Show the requested ssh key in view.
    """
    key = SSHKey.select().where(SSHKey.id == id).get()

    data = [
        ['ID', id],
        ['Name', key.name],
        ['Active', 'Y' if key.active else 'N']
    ]
    table = AsciiTable(data)
    click.echo(table.table)
    click.pause()
    click.edit(key.data.tobytes().decode('utf-8'), editor='view')


@keys.command()
@click.argument('id', metavar='ID', type=click.INT)
@click.argument('file', metavar='FILE', type=click.File('wb'))
def get(id, file):
    """
    Retrieve and locally save a key.

    FILE may be a local file path to save the requested key or - to
    write the key's contents to stdout.
    """
    key = SSHKey.select().where(SSHKey.id == id).get()
    file.write(key.data)


@keys.command()
@click.argument('id', metavar='ID', type=click.INT)
def rm(id):
    """
    Delete the given ssh key.
    """
    SSHKey.delete().where(SSHKey.id == id).execute()
