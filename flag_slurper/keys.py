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
    if team:
        team = Team.get_by_id(team)

    Key.create(team=team, username=username, contents=file.read())
    utils.report_success(f'Key for user {username} created successfully')
