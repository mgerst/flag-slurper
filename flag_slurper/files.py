import click
from terminaltables import AsciiTable

from .autolib.models import database_proxy, File, Service, Team
from .project import Project
from . import utils


@click.group()
@click.pass_context
def files(ctx):
    """
    View and managed files found with autopwn or manually.
    """
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("File commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


@files.command()
@click.option('-t', '--team', type=click.INT, help="Filter by team number", default=None)
@click.option('-n', '--name', type=click.STRING, help="Filter by filename", default=None)
@click.option('-s', '--service', type=click.STRING, help="Filter by service name", default=None)
def ls(team, name, service):
    """
    List all files found by autopwn.
    """
    with database_proxy.obj:
        files = File.select().join(Service).join(Team)

        if team:
            files = files.where(File.service.team.number == team)

        if name:
            files = files.where(File.path.contains(name))

        if service:
            files = files.where(File.service.service_name.contains(service))

        if files.count() == 0:
            utils.report_warning("No files found")
            exit(1)

        data = [[f.id, f.path, f.info, f.service.team.number, f.service.service_name] for f in files]
        data.insert(0, ['ID', 'Path', 'Info', 'Team Number', 'Service'])
        table = AsciiTable(data)
        utils.conditional_page(table.table, len(data))


@files.command()
@click.argument('id', metavar='ID', type=click.INT)
def show(id):
    """
    Show the requested file in view.
    """
    file = File.select().where(File.id == id).get()

    data = [
        ['ID', id],
        ['Path', file.path],
        ['Info', file.info],
        ['Mime Type', file.mime_type],
        ['Team', file.service.team.number],
        ['Service', file.service.service_name],
    ]
    table = AsciiTable(data)
    click.echo(table.table)
    click.pause()

    if 'text' in file.info:
        click.edit(file.contents.tobytes().decode('utf-8'), editor='view')


@files.command()
@click.argument('id', metavar='ID', type=click.INT)
@click.argument('file', metavar='FILE', type=click.File('wb'))
def get(id, file):
    """
    Retrieve and localy save a file.

    FILE may be a local file path to save the requested file or - to
    write the file's contents to stdout.
    """
    f = File.select().where(File.id == id).get()
    file.write(f.contents)


@files.command()
@click.argument('id', metavar='ID', type=click.INT)
def rm(id):
    """
    Delete the given file.
    """
    File.delete().where(File.id == id).execute()
