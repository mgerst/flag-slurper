import zipfile
from typing import Tuple, Dict, Union, Callable

import click
import requests

from .config import Config
from .models import User


def get_user() -> User:
    conf = Config.get_instance()
    extras = conf.request_extras()
    url = '{}/user/show.json'.format(conf.api_url)
    resp = requests.get(url, **extras)
    if resp.status_code == 403:
        report_error('Unauthorized: Invalid authentication information')
        exit(1)
    resp.raise_for_status()
    resp = resp.json()
    return User(resp)


def check_user(user):
    if not user.is_red_or_admin:
        report_error('This command is only avialable to red team and admin users')
        exit(2)


def get_flags(team=None):
    conf = Config.get_instance()
    extras = conf.request_extras()
    url = '{}/flags.json'.format(conf.api_url)

    if team:
        url = '{}?team_number={}'.format(url, team)

    resp = requests.get(url, **extras)
    resp.raise_for_status()
    resp = resp.json()

    if team:
        resp = list(filter(lambda x: x['team_number'] == team, resp))

    return resp


def save_flags(flags, team=None):
    if team:
        filename = 'team_{}_flags.zip'.format(team)
    else:
        filename = 'all_team_flags.zip'

    z = zipfile.ZipFile(filename, 'a', compression=zipfile.ZIP_DEFLATED)

    for flag in flags.values():
        flags['data'] += '\n'
        z.writestr(flag['filename'], flag['data'])

    for zipped_file in z.filelist:
        zipped_file.create_system = 0
    z.close()


def report_error(msg):
    msg = '{} {}'.format(click.style('[!]', fg='red'), msg)
    click.echo(msg)


def report_status(msg):
    msg = '{} {}'.format(click.style('[-]', fg='cyan'), msg)
    click.echo(msg)


def report_warning(msg):
    msg = '{} {}'.format(click.style('[*]', fg='yellow'), msg)
    click.echo(msg)


def report_success(msg):
    msg = '{} {}'.format(click.style('[+]', fg='green'), msg)
    click.echo(msg)


def parse_remote(remote: str) -> Tuple[str, str, int]:
    username = 'root'
    port = 22

    parts = remote.split('@')
    if len(parts) > 1:
        username = parts[0]
        parts = parts[1:]

    parts = parts[0].split(':')
    host = parts[0]
    if len(parts) > 1:
        port = int(parts[1])

    return username, host, port


def prompt_choice(template: str, info: Dict[id, Dict], prompt: str = None, title: str = None) -> int:
    if title:
        click.echo(title)

    for i, item in info.items():
        click.echo(template.format(i=i, info=item))

    if not prompt:
        prompt = "Selection"
    chosen = click.prompt(prompt, type=click.INT)

    return chosen
