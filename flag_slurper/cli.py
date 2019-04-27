import code

import click
import pathlib

from . import __version__
from . import utils
from .config import Config
from .project import Project

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}

pass_conf = click.make_pass_decorator(Config)


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('-c', '--config', type=click.Path(), envvar='CONFIG_FILE')
@click.option('--iscore-url', envvar='ISCORE_URL', default=None)
@click.option('--api-token', envvar='ISCORE_API_TOKEN', default=None)
@click.option('-p', '--project', envvar='SLURPER_PROJECT', type=click.Path(), default=None)
@click.option('-np', '--no-project', is_flag=True)
@click.option('-d', '--debug', count=True)
@click.version_option(version=__version__, prog_name='flag-slurper')
@click.pass_context
def cli(ctx, config, iscore_url, api_token, project, debug, no_project):
    ctx.obj = Config.load(config)
    ctx.obj.cond_set('iscore', 'url', iscore_url)
    ctx.obj.cond_set('iscore', 'api_token', api_token)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    if project and not no_project:
        project = pathlib.Path(project)
        project = project.expanduser()
        if project.is_dir():
            project = project / 'project.yml'
        p = Project.get_instance()
        p.load(str(project))

    if debug:  # pragma: no cover
        import logging
        if debug > 1:
            logger = logging.getLogger("peewee")
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())

        logger = logging.getLogger('flag_slurper')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())


@cli.command()
@click.option('-t', '--team', type=click.INT, default=None)
@pass_conf
def plant(conf, team):
    user = conf.user
    utils.check_user(user)

    if not team:
        team = click.prompt('Which team do you want to get flags for?', prompt_suffix='\n> ', default=-1)

    team = None if team < 0 else team
    click.echo('Team: {}'.format(team))

    flags = utils.get_flags(team)
    flags = {i: x for i, x in enumerate(flags)}

    click.echo('Pick the flag to place')
    for flag_id, flag in flags.items():
        # Admins can see both blue and red flags, tell them which is which
        if user.is_admin:
            click.echo('{}. {} ({})'.format(flag_id, flag['name'], flag['type']))
        else:
            click.echo('{}. {}'.format(flag_id, flag['name']))

    flag = click.prompt('Which Flag', type=click.INT)
    if flag not in flags:
        utils.report_error('Invalid selection: {}'.format(flag))
        exit(1)
    flag = flags[flag]
    click.echo('Flag: {}'.format(flag['data']))


@cli.command()
@pass_conf
def shell(config):
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("The shell requires an active project")
        exit(4)
    p.connect_database()

    from . import autolib

    gl = {
        'project': p,
        'Project': Project,
        'config': config,
        'Config': Config,
        'autolib': autolib,
    }

    import inspect
    modellist = inspect.getmembers(autolib.models, inspect.isclass)
    modellist = {x[0]: x[1] for x in modellist}
    gl.update(modellist)

    code.InteractiveConsole(locals=gl).interact()


# Load additional commands
from .config import config
from .credentials import creds
from .dns import dns
from .project import project
from .teams import team
from .services import service
from .files import files
from .notes import notes
cli.add_command(config)
cli.add_command(creds)
cli.add_command(dns)
cli.add_command(project)
cli.add_command(team)
cli.add_command(service)
cli.add_command(files)
cli.add_command(notes)

# Feature detect remote functionality
try:
    import paramiko  # noqa
    from .remote import remote
    from .autopwn import autopwn
    cli.add_command(remote)
    cli.add_command(autopwn)
except ImportError:  # pragma: no cover
    pass
