import click
from terminaltables import AsciiTable

from .autolib.models import database_proxy, CaptureNote, Service, Team, Flag
from .project import Project
from . import utils


@click.group()
@click.pass_context
def notes(ctx):
    """
    View and manage capture notes created by autopwn or manually.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error('Capture note commands require an active project')
        exit(4)
    p.connect_database()
    ctx.obj = p


@notes.command()
@click.option('-t', '--team', type=click.INT, help='Filter by team number', default=None)
@click.option('-s', '--service', type=click.STRING, help='Filter by service name', default=None)
def ls(team, service):
    """
    List all capture notes found by autopwn.
    """
    with database_proxy.obj:
        notes = CaptureNote.select().join(Service).join(Team).join(Flag)

        if team:
            notes = notes.where(CaptureNote.service.team.number == team)

        if service:
            notes = notes.where(CaptureNote.service.service_name.contains(service))

        if notes.count() == 0:
            utils.report_warning('No capture notes found')
            exit(1)

        def _username(cred):
            if cred:
                return cred.bag.username
            return None

        data = [[n.id, n.flag.name, n.notes, n.searched, n.location, _username(n.used_creds)] for n in notes]
        data.insert(0, ['ID', 'Flag', 'Notes', 'searched', 'location', 'used_creds'])
        table = AsciiTable(data)
        utils.conditional_page(table.table, len(data))


@notes.command()
@click.argument('id', metavar='ID', type=click.INT)
def show(id):
    """
    Show the requested capture note.
    """
    try:
        note = CaptureNote.select().where(CaptureNote.id == id).get()
    except CaptureNote.DoesNotExist:
        utils.report_error('Capture note {id} does not exist'.format(id=id))
        exit(1)

    data = [
        ['ID', note.id],
        ['Flag', note.flag.name],
        ['Searched', note.searched],
        ['Location', note.location],
        ['Data', note.data],
    ]

    if note.used_creds:
        data.append(['Used Creds', note.used_creds.bag])

    data.append(['Notes', note.notes])

    table = AsciiTable(data)
    click.echo(table.table)
