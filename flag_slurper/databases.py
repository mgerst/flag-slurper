import click
from terminaltables import AsciiTable

from . import utils
from .autolib.models import database_proxy, Database, Service, Team
from .conf.project import Project, pass_project


@click.group()
@click.pass_context
def databases(ctx):
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error('Database commands require an active project')
        exit(4)
    p.connect_database()
    ctx.obj = p


@databases.command()
@click.option('-t', '--team', type=click.INT, help='Filter by team number', default=None)
@click.option('-s', '--service', type=click.STRING, help='Filter by service name', default=None)
def ls(team, service):
    """
    List all databases found by autopwn.
    """
    with database_proxy.obj:
        dbs = Database.select().join(Service).join(Team)

        if team:
            dbs = dbs.where(Database.service.team.number == team)

        if service:
            dbs = dbs.where(Database.server.service_name.contains(service))

        if dbs.count() == 0:
            utils.report_warning('No files found')
            exit(1)

        data = [[d.id, d.type, d.version, d.service.team.number, d.service.service_name, d.username, d.password] for d in dbs]
        data.insert(0, ['ID', 'Type', 'Version', 'Team Number', 'Service', 'Username', 'Password'])
        table = AsciiTable(data)
        utils.conditional_page(table.table, len(data))
