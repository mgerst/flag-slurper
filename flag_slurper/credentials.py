import click

from . import utils
from .autolib.models import database_proxy, CredentialBag
from .project import Project

pass_project = click.make_pass_decorator(Project)


@click.group()
@click.pass_context
def creds(ctx):
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("Credentials commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


@creds.command()
@click.argument('username')
@click.argument('password')
def add(username, password):
    with database_proxy.obj:
        c = CredentialBag.create(username=username, password=password)
        utils.report_success("Added {}:{}".format(c.username, c.password))


@creds.command()
def ls():
    with database_proxy.obj:
        creds = CredentialBag.select()
        click.echo("Username:Password")
        for cred in creds:
            click.echo("{}:{}".format(cred.username, cred.password))


@creds.command()
@click.argument('username')
@click.argument('password', required=False)
def rm(username, password):
    with database_proxy.obj:
        if password:
            query = CredentialBag.delete().where(CredentialBag.username == username, CredentialBag.password == password)
        else:
            query = CredentialBag.delete().where(CredentialBag.username == username)
        query.execute()


@creds.command()
@click.argument('cred')
def show(cred):
    """
    Show the credential given by CRED, where CRED follows the format <username>[:<password>].
    """
    username, password = utils.parse_creds(cred)
    query = CredentialBag.select().where(CredentialBag.username == username)
    if password:
        query = query.where(CredentialBag.password == password)

    for bag in query:
        click.echo("Credential: {}:{}".format(bag.username, bag.password))

        click.echo("------------ [ Found Credentials ] ------------")

        for cred in bag.credentials:
            click.echo("{team}/{url}:{port}: {status}".format(
                team=cred.service.team.number,
                url=cred.service.service_url,
                port=cred.service.service_port,
                status=cred.state,
            ))

        if len(bag.credentials) == 0:
            click.echo("This credential bag has no hits")

        click.echo("\n\n")

    if len(query) == 0:
        click.echo("No credentials matching this query")
        exit(3)
