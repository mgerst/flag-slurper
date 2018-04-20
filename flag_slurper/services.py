import click
from terminaltables import AsciiTable

from . import utils
from .autolib.models import database_proxy, Service, Team
from .project import Project


@click.group()
@click.pass_context
def service(ctx):
    """
    Manage services.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("service commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


@service.command()
@click.option('-t', '--team', default=None)
def ls(team):
    """
    List all services.
    """
    query = Service.select(Service.id, Team.number, Service.service_name, Service.service_port, Service.service_url,
                           Service.is_rand, Service.high_target, Service.low_target).join(Team)
    if team:
        query = query.where(Service.team == team)

    services = [
        [s.id, s.team.number, s.service_name, s.service_port, s.service_url, s.is_rand, s.high_target, s.low_target] for
        s in query]
    services.insert(0, ['ID', 'Team', 'Name', 'Port', 'URL', 'Random?', 'High', 'Low'])
    table = AsciiTable(services)
    utils.conditional_page(table.table, len(services))


@service.command()
@click.argument('id')
@click.argument('name')
@click.option('-p', '--port', required=True)
@click.option('-u', '--url', required=True)
@click.option('-a', '--admin', type=click.Choice(['DOWN', 'CAPPED']), default=None)
@click.option('-r', '--is-rand', is_flag=True, default=False)
@click.option('-i', '--high', default=None)
@click.option('-l', '--low', default=None)
@click.option('-t', '--team', required=True)
def add(id, name, port, url, admin, is_rand, high, low, team):
    with database_proxy.obj:
        Service.create(id=id, remote_id=id, service_id=id, service_name=name, service_port=port, service_url=url,
                       service_admin=admin, is_rand=is_rand, high=high, low=low, team=team)
        click.secho('Service added.', fg='green')


@service.command()
@click.argument('id')
def rm(id):
    with database_proxy.obj:
        Service.delete().where(Service.id == id).execute()
        click.secho('Service removed.', fg='red')
