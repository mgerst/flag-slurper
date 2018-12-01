import os
import shutil
import zipfile
from typing import Tuple, Dict, Union, Callable, Optional
import string

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


def save_flags(flags, team=None, base_path=None):
    if team:
        filename = 'team_{}_flags.zip'.format(team)
    else:
        filename = 'all_team_flags.zip'

    if base_path:
        filename = os.path.join(base_path, filename)

    z = zipfile.ZipFile(filename, 'a', compression=zipfile.ZIP_DEFLATED)

    for flag in flags.values():
        flag['data'] += '\n'
        z.writestr(flag['filename'], flag['data'])

    for zipped_file in z.filelist:
        zipped_file.create_system = 0
    z.close()


def get_teams() -> list:
    conf = Config.get_instance()
    url = '{}/teams.json'.format(conf.api_url)

    resp = requests.get(url)
    resp.raise_for_status()
    resp = resp.json()
    return resp


def get_team_map(teams):
    map = {team['number']: team for team in teams}
    return map


# TODO: Should be using the /services.json endpoint but it's currently 500'ing
def get_service_status() -> list:
    conf = Config.get_instance()
    url = '{}/servicestatus.json'.format(conf.api_url)

    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def get_services() -> list:
    conf = Config.get_instance()
    url = '{}/services.json'.format(conf.api_url)

    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def get_service(name) -> dict:
    """
    Get a service by its name.

    .. note::

        The IScorE API changed and the service_id returned by service status
        cannot be used to find the service. As a temporary workaround, we are
        matching on service name, which ***should*** be unique.

    :param name: The name of the service
    :return: The matched service.
    """
    if not hasattr(get_service, 'service_cache'):
        get_service.service_cache = {s['name']: s for s in get_services()}
    return get_service.service_cache[name]


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


def parse_creds(creds: str) -> Tuple[str, Optional[str]]:
    if ':' not in creds:
        return creds, None
    username, password = creds.split(':')
    return username, password


def should_page(size: int) -> bool:
    """
    Determine whether to page output.

    :param size: The size of the output (in lines)
    :return: True if should page, False otherwise
    """
    term_size = shutil.get_terminal_size((80, 20))
    return term_size.lines < size


def conditional_page(output: str, size: int):
    if should_page(size):
        click.echo_via_pager(output)
    else:
        click.echo(output)


def parse_duration(duration: str) -> int:
    """
    Parses a duration of the form 10m or 5s and converts
    them into seconds.

    >>> parse_duration('5s')
    ... 5
    >>> parse_duration('10m')
    ... 600

    .. note::

       Only one unit is supported. For example 1h30m is not supported, but 90m is.

    Supported suffixes:

    - ``h`` hours
    - ``m`` minutes
    - ``s`` seconds

    An omitted suffix will be interpreted as seconds.

    :param duration: The duration in string form
    :return: The duration in seconds
    """
    if len(duration) == 0:
        raise ValueError("Unable to parse empty duration")

    if duration[-1] in string.digits:
        return int(duration)

    if duration[-1].lower() == 'h':
        return int(duration[:-1]) * 60 * 60

    if duration[-1].lower() == 'm':
        return int(duration[:-1]) * 60

    if duration[-1].lower() == 's':
        return int(duration[:-1])

    raise ValueError("Unable to parse {duration} as a duration".format(duration=duration))
