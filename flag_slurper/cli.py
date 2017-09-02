import click

from . import __version__
from . import utils
from .config import Config

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}

pass_conf = click.make_pass_decorator(Config)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-c', '--config', type=click.Path(), envvar='CONFIG_FILE')
@click.option('--iscore-url', envvar='ISCORE_URL', default=None)
@click.option('--api-token', envvar='ISCORE_API_TOKEN', default=None)
@click.pass_context
def cli(ctx, config, iscore_url, api_token):
    ctx.obj = Config.load(config)
    ctx.obj.cond_set('iscore', 'url', iscore_url)
    ctx.obj.cond_set('iscore', 'api_token', api_token)
    click.echo('Flag Slurper v{}'.format(__version__))


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

# Feature detect remote functionality
try:
    import paramiko  # noqa
    from .remote import remote
    cli.add_command(remote)
except ImportError:
    pass
