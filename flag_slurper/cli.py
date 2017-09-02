from . import __version__
from .config import Config

import click

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}

pass_conf = click.make_pass_decorator(Config)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-c', '--config', type=click.Path(), envvar='CONFIG_FILE')
@click.pass_context
def cli(ctx, config):
    ctx.obj = Config.load(config)
    print('Flag Slurper v{}'.format(__version__))
