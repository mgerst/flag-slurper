import click
from terminaltables import AsciiTable

from . import utils
from .autolib.models import database_proxy, Service, Team
from flag_slurper.conf.project import Project


@click.group()
@click.pass_context
def services(ctx):
    """
    Manage services.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("service commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


@services.command()
@click.option('-t', '--team', default=None)
def ls(team):
    """
    List all services.
    """
    query = Service.select(Service.id, Team.number, Service.service_name, Service.service_port, Service.service_url,
                           Service.is_rand, Service.high_target, Service.low_target).join(Team)
    if team:
        query = query.where(Service.team.number == team)

    services = [
        [s.id, s.team.number, s.service_name, s.service_port, s.service_url, s.is_rand, s.high_target, s.low_target] for
        s in query]
    services.insert(0, ['ID', 'Team', 'Name', 'Port', 'URL', 'Random?', 'High', 'Low'])
    table = AsciiTable(services)
    utils.conditional_page(table.table, len(services))


@services.command()
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
    Service.create(id=id, remote_id=id, service_id=id, service_name=name, service_port=port, service_url=url,
                   service_admin=admin, is_rand=is_rand, high=high, low=low, team=team)
    utils.report_success('Service added')


@services.command()
@click.argument('name')
@click.option('-p', '--port', type=click.INT, required=True)
@click.option('-u', '--url', type=click.STRING, required=True,
              help='You may use {num} to replace the team number in the URL')
@click.option('-r', '--is-rand', is_flag=True, default=False)
@click.option('-i', '--high', type=click.INT, default=None)
@click.option('-l', '--low', type=click.INT, default=None)
def mass_add(name: str, port: int, url: str, is_rand: bool, high: int, low: int):
    """
    Add a service to all teams.
    """
    for team in Team.select():
        Service.create(service_name=name, service_port=port, service_url=url.format(num=team.number), is_rand=is_rand,
                       high=high, low=low, team=team)
    utils.report_success(f'Mass added service {name}')


@services.command()
@click.argument('id')
@click.option('-n', '--name', 'service_name', default=None)
@click.option('-p', '--port', 'service_port', default=None)
@click.option('-u', '--url', 'service_url', default=None)
@click.option('-a', '--admin', 'admin_status', type=click.Choice(['DOWN', 'CAPPED']), default=None)
@click.option('-r', '--is-rand', type=click.BOOL, default=None)
@click.option('-i', '--high', 'high_target', default=None)
@click.option('-l', '--low', 'low_target', default=None)
def edit(id, **kwargs):
    updates = {key: value for (key, value) in kwargs.items() if value is not None}
    Service.update(**updates).where(Service.id == id).execute()
    utils.report_success(f'Updated service {id}')


@services.command()
@click.argument('id')
def rm(id):
    Service.delete().where(Service.id == id).execute()
    click.secho('Service removed.', fg='red')
