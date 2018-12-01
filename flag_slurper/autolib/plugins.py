import logging
from abc import ABC, abstractmethod
from typing import Dict, Type, List

from schema import Schema

from .models import Service

logger = logging.getLogger(__name__)


class PluginContext(dict):
    """
    A wrapper method for passing plugin methods arbitrary data.

    This allows plugins to be passed whatever arbitrary data they
    need onto the plugins in an extensible way.
    """

    def validate(self, schema: dict) -> 'PluginContext':
        """
        Allow a plugin to enforce their own schema for
        their context data. The ``Schema`` object is
        created by the context, not the plugin.

        :param schema: A dictionary containing the schema
        :return: Returns the context for chaining
        """
        Schema(schema, ignore_extra_keys=True).validate(self)
        return self


class Plugin(ABC):
    """
    Defines an autolib plugin.

    Plugins are configured in the project. For example:

    .. code-block:: yaml

        ---
        _version: "0.1"
        ...
        <type>:
          - service: WWW SSH
            commands:
              - <post plugin name>:
                  <arguments>
    """
    name = None
    schema = None
    context_schema = None
    config = None
    type = None

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

        This is used between runs.
        """
        self.config = None

    @abstractmethod
    def run(self, service: Service, context: PluginContext) -> bool:
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
    def predicate(self, service: Service, context: PluginContext) -> bool:
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
    The plugin registry.

    This handles configuring and figuring out which plugins will
    need to be run.
    """
    type = None

    def __init__(self):
        self.registry: Dict[str, Plugin] = {}

    def register(self, plugin: Type[Plugin]):
        """
        Register a plugin with the plugin registry.

        :param plugin: The plugin class to register.
        :raises ValueError: If the plugin does not subclass :py:class:`Plugin`
        :raises ValueError: If the plugin name is already taken.
        """
        if not issubclass(plugin, Plugin):
            raise ValueError('Plugins must extend Plugin')
        if plugin.name in self.registry:
            raise ValueError('Plugin already registered by this name: {}'.format(plugin.name))
        self.registry[plugin.name] = plugin()

        # The plugins that will be used for the current run
        self.run_plugins = []

    def configure(self, config: List[dict]):
        """
        Configure the plugins that will be used for this run.

        This will accept the ``commands`` section for the currents ervice.

        :param config: The config for the current service.
        :raises KeyError: When a command is specified that doesn't exist.
        :raises ValueError: When more than one key in a command entry.
        :raises ValueError: When a command uses an unknown plugin.
        """

        # Unconfigure all plugins from a previous run
        list(map(Plugin.unconfigure, self.registry.values()))
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

    def post(self, service: Service, context: PluginContext) -> bool:
        """
        Runs applicable plugins against the given service,
        with the given context.

        :param service: The service to run against
        :param context: THe context for the service
        :return: Whether all invocations were successful
        """
        results = [plugin.run(service, context)
                   for plugin in self.registry.values()
                   if plugin.name in self.run_plugins or plugin.predicate(service, context)]
        return all(results)
