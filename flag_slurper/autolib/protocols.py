from typing import Tuple

import paramiko


def _get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def pwn_ssh(url: str, port: int) -> Tuple[str, bool, bool]:
    ssh = _get_ssh_client()

    try:
        ssh.connect(url, port=port, username='root', password='cdc')
        return 'Found valid user: root', True, False
    except:
        try:
            ssh.connect(url, port=port, username='cdc', password='cdc')
            return 'Found valid user: cdc', True, False
        except:
            return 'Authentication failed', False, False


PWN_FUNCS = {
    'ssh': pwn_ssh,
}

