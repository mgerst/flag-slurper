import click
from terminaltables import AsciiTable

from . import utils
from .autolib.models import database_proxy, Team
from .project import Project

pass_project = click.make_pass_decorator(Project)


@click.group()
@click.pass_context
def team(ctx):
    """
    Perform operations on teams.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("teams commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


@team.command()
@click.argument('name')
@click.argument('number')
@click.argument('domain')
def add(name, number, domain):
    """
    Add team.
    """
    with database_proxy.obj:
        Team.create(id=number, name=name, number=number, domain=domain)
        click.secho("Team added.", fg='green')


@team.command()
@click.argument('number')
def rm(number):
    """
    Remove a team.
    """
    with database_proxy.obj:
        Team.delete().where(Team.number == number).execute()
        click.secho("Team removed.", fg='red')


@team.command()
def ls():
    """
    List all found teams.
    """
    with database_proxy.obj:
        teams = Team.select()
        teamdata = [[t.number, t.name, t.domain] for t in teams]
        teamdata.insert(0, ['Number', 'Name', 'Domain'])
        table = AsciiTable(teamdata)
        utils.conditional_page(table.table, len(teamdata))


@team.command()
@click.argument('team_number')
def show(team_number):
    t = Team.select().where(Team.number == team_number).get()
    click.echo("Id: {}".format(t.id))
    click.echo("Number: {}".format(t.number))
    click.echo("Name: {}".format(t.name))
    click.echo("Domain: {}".format(t.domain))

    services = [[s.id, s.service_name, s.service_port, s.service_url] for s in t.services]
    services.insert(0, ['ID', 'Name', 'Port', 'URL'])

    if utils.should_page(len(services) - 3):
        click.pause('---- Services (Press any key to show) ----')

    table = AsciiTable(services)
    utils.conditional_page(table.table, len(services) - 3)
