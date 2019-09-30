from configparser import ConfigParser
from pathlib import Path

import click

ROOT = Path(__file__).parent


@click.group()
def config():
    pass


@config.command()
@click.option('-t', '--token', prompt=True, hide_input=True, help='An explicit api token')
@click.option('-c', '--config', default='~/.flagrc', help='flagrc to save token to')
def login(token, config):
    flagrc = Path(config)
    click.echo("Writing token to {}".format(flagrc))
    flagrc = flagrc.expanduser()

    c = ConfigParser()
    c.read(str(flagrc))

    if not c.has_section('iscore'):
        c.add_section('iscore')

    c['iscore']['api_token'] = token
    with flagrc.open('w') as fp:
        c.write(fp)
