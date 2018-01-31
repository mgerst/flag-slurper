import os
from io import BytesIO

import click
import paramiko

from . import utils, autolib
from .config import Config

pass_config = click.make_pass_decorator(Config)


@click.group()
def remote():
    pass


@remote.command()
@click.option('-t', '--team', type=click.INT, default=None)
@click.option('-f', '--flag-id', type=click.INT, default=None)
@click.option('-F', '--flag-name', default=None)
@click.option('-l', '--location', default=None)
@click.option('-P', '--password', default='cdc', envvar='REMOTE_PASS')
@click.option('-W', '--prompt-password', is_flag=True)
@click.argument('remote')
@pass_config
def plant(conf, team, flag_id, flag_name, location, password, prompt_password, remote):
    user = conf.user
    utils.check_user(user)

    if not team:
        team = click.prompt('Which team do you want to get flags for?', prompt_suffix='\n> ', default=-1)

    team = None if team < 0 else team
    utils.report_status('Finding flags for team {}'.format(team))

    flags = utils.get_flags(team)
    flags = {i: x for i, x in enumerate(flags)}

    flag = None
    if flag_name:
        flags = {i: flag for i, flag in flags.items() if flag['name'] == flag_name}
        if len(flags) == 0:
            utils.report_error("No flag by name: {}".format(flag_name))
            exit(1)
        elif len(flags) == 1:
            flag = list(flags.keys())[0]
        else:
            tmpl = "{i}. {info.name}"
            if user.is_admin:
                tmpl = "{i}. {info.name} ({info.type})"
            flag = utils.prompt_choice(tmpl, flags, "Which Flag", "Pick the flag to place")
    elif flag_id is None:
        tmpl = "{i}. {info.name}"
        if user.is_admin:
            tmpl = "{i}. {info.name} ({info.type})"

        flag = utils.prompt_choice(tmpl, flags, "Which Flag", "Pick the flag to place")
    else:
        utils.report_status('Flag supplied from command line')
        flag = flag_id

    if flag not in flags:
        utils.report_error('Invalid selection: {}'.format(flags))
        exit(1)
    flag = flags[flag]
    data = flag['data']
    filename = flag['filename']

    if not location:
        location = click.prompt('Enter the remote location', default='/root')
    else:
        utils.report_status('Location supplied from command line')
    location = os.path.join(location, filename)

    # Remote Section
    if prompt_password:
        password = click.prompt('Remote Password', hide_input=True)
    username, host, port = utils.parse_remote(remote)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password, port=port)

    pkt = BytesIO()
    pkt.write(data.encode('utf-8'))
    pkt.write(b'\n')
    pkt.seek(0)

    sftp = ssh.open_sftp()
    sftp.putfo(pkt, location)
    utils.report_status('Verifying flag plant')

    planted_contents = autolib.exploit.get_file_contents(ssh, location)

    if planted_contents != data:
        utils.report_warning('Planted flag data does not match, double check the plant')
    else:
        utils.report_success('Flag Planted')


@remote.command()
@click.option('-t', '--team', help='Team number', default=None, prompt=True)
@click.option('-f', '--flag', help='Flag Slug', default=None, prompt=True)
@click.option('-l', '--location', default=None, prompt=True)
@click.option('-P', '--password', default='cdc', envvar='REMOTE_PASS')
@click.option('-W', '--prompt-password', is_flag=True)
@click.option('-s', '--search', help='Force search for flag', is_flag=True)
@click.argument('remote')
@pass_config
def capture(conf, team, flag, location, password, prompt_password, remote, search):
    user = conf.user
    utils.check_user(user)

    filename = 'team{}_{}.flag'.format(team, flag)
    base_dir = location
    location = os.path.join(location, filename)
    search_glob = os.path.join(base_dir, '*flag*')

    if prompt_password:
        password = click.prompt('Remote Password', hide_input=True)
    username, host, port = utils.parse_remote(remote)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password, port=port)

    planted = autolib.exploit.get_file_contents(ssh, location)
    if not planted or search:
        _, stdout, stderr = ssh.exec_command('ls {}'.format(search_glob))

        files = []
        for line in stdout.read().splitlines():
            files.append(line.decode('utf-8'))

        print("Found possible flags:", ', '.join(files))
        for file in files:
            utils.report_status('Checking possible flag: {}'.format(file))
            contents = autolib.exploit.get_file_contents(ssh, file)
            if not contents:
                utils.report_warning('File {} does not contain flag'.format(file))
            elif 10 < len(contents) < 60:
                utils.report_success('Possible Flag {}: {}'.format(file, contents))
            else:
                utils.report_warning('File {} incorrect size for flag'.format(file))
    else:
        utils.report_success('Found Flag: {}'.format(planted))


@remote.command()
@click.option('-P', '--password', default='cdc', envvar='REMOTE_PASS')
@click.option('-W', '--prompt-password', is_flag=True)
@click.argument('remote')
def infect(password, prompt_password, remote):
    if prompt_password:
        password = click.prompt('Remote Password', hide_input=True)
    username, host, port = utils.parse_remote(remote)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password, port=port)

    _, stdout, stderr = ssh.exec_command('pip install --user flag-bearer')
    err = stderr.read()
    if len(err) > 0:
        utils.report_error('Failed to install flag-bearer')
    else:
        utils.report_success('Installed flag-bearer')
