import click
from terminaltables import AsciiTable


from .autolib.models import database_proxy, DNSResult, Service, Team
from .project import Project
from . import utils


@click.group()
@click.pass_context
def dns(ctx):
    """
    View and manage dns records found with autopwn.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("DNS commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


@dns.command()
@click.option('-t', '--team', type=click.INT, help="Filter by team number", default=None)
def ls(team):
    """
    List all files found by autopwn.
    """
    with database_proxy.obj:
        records = DNSResult.select().join(Team)

        if team:
            records = records.where(DNSResult.team.number == team)

        if records.count() == 0:
            utils.report_warning("No records found for team {}".format(team))
            exit(1)

        data = [[r.id, r.team.number, r.name, r.record] for r in records]
        data.insert(0, ['ID', 'Team', 'Name', 'Record'])
        table = AsciiTable(data)
        utils.conditional_page(table.table, len(data))
