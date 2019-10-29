import click
from terminaltables import AsciiTable

from flag_slurper import utils
from flag_slurper.autolib.models import Key, Team
from flag_slurper.conf import Project


@click.group()
@click.pass_context
def keys(ctx):
    """
    View and manage ssh private keys to be used with autopwn.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error('Key commands require an active project')
        exit(4)
    p.connect_database()
    ctx.obj = p


@keys.command()
@click.option('-t', '--team', type=click.INT, help='Filter by team number', default=None)
@click.option('-u', '--username', type=click.STRING, help='Filter by username', default=None)
def ls(team, username):
    """
    List all keys used by autopwn.
    """
    keys = Key.select()

    if team:
        keys = keys.join(Team).where(Key.team.number == team)

    if username:
        keys = keys.where(Key.username == username)

    if keys.count() == 0:
        utils.report_warning('No keys found')
        exit(1)

    data = [[k.id, k.username, k.team.number if k.team else ''] for k in keys]
    data.insert(0, ['ID', 'Username', 'Team'])
    table = AsciiTable(data)
    utils.conditional_page(table.table, len(data))


@keys.command()
@click.argument('file', type=click.File('r'))
@click.option('-t', '--team', type=click.INT)
@click.option('-u', '--username', type=click.STRING, required=True)
def add(file, team, username):
    """
    Add an ssh key to use for autopwn.
    """
    if team:
        team = Team.get_by_id(team)

    Key.create(team=team, username=username, contents=file.read())
    utils.report_success(f'Key for user {username} created successfully')


@keys.command()
@click.argument('id', metavar='ID', type=click.INT)
def show(id):
    """
    Show the requested SSH key in view.
    """
    key = Key.get_by_id(id)

    data = [
        ['ID', id],
        ['Username', key.username],
        ['Team Number', key.team.number if key.team else ''],
        ['Team Name', key.team.name if key.team else ''],
    ]
    table = AsciiTable(data)
    click.echo(table.table)
    click.pause()
    click.edit(key.contents, editor='view')


@keys.command()
@click.argument('id', metavar='ID', type=click.INT)
@click.argument('file', metavar='FILE', type=click.File('wb'))
def get(id, file):
    """
    Retrieve and locally save a private key.

    FILE may be a local file path to save the key or - to
    write the keys' contents to stdout.
    """
    key = Key.get_by_id(id)
    file.write(key.contents.encode('utf-8'))


@keys.command()
@click.argument('id')
def rm(id):
    """
    Remove an SSH key.
    """
    Key.delete().where(Key.id == id).execute()
    click.secho('Key removed.', fg='red')
