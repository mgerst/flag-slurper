import click

from .formatters import display_format
from .. import utils
from ..autolib.models import database_proxy, ShadowEntry, Service, Team, File
from ..conf.project import Project


@click.group()
@click.pass_context
def shadow(ctx):
    """
    View and manage shadow file entries found with autopwn.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("Shadow commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


@shadow.command()
@click.option('-t', '--team', type=click.INT, help="Specify a team number", default=None)
@click.option('-s', '--service', type=click.STRING, help="The", default=None)
@click.option('-u', '--username', type=click.STRING, help="", default=None)
@click.option('-f', '--format', type=click.Choice(['table', 'hashcat', 'txt'], case_sensitive=True), default='table')
def ls(team, service, username, format):
    with database_proxy:
        shadows = ShadowEntry.select().join(Service).join(Team)

        if team:
            shadows = shadows.where(ShadowEntry.service.team.number == team)

        if service:
            shadows = shadows.where(ShadowEntry.service.service_name.contains(service))

        if username:
            shadows = shadows.where(ShadowEntry.username.contains(service))

        if shadows.count() == 0:
            utils.report_warning("No shadow entries found")
            exit(1)

        display_format(shadows, format)
