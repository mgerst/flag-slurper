import typing as tp
from copy import deepcopy
from pathlib import Path

import click
import yaml
from jinja2 import Environment
from schema import Schema, Use, Optional
from yaml import safe_load

from flag_slurper.config import Config
from . import utils
from .autolib import models

project_schema_v1_0 = Schema({
    '_version': Use(str, error='Must include _version'),
    'project': str,
    'base': Use(Path, error='base must be a path'),
    Optional('results'): Use(Path, error='results must be a path'),
    Optional('teams'): Use(Path, error='teams must be a path'),
    Optional('services'): Use(Path, error='services must be a path'),
    Optional('flags'): Schema([
        {
            'service': str,
            'type': lambda x: x in ['blue', 'red'],
            'location': str,
            'name': str,
            'search': bool,
        }
    ]),
    Optional('post', default=[]): Schema([
        {
            'service': str,
            'commands': Schema([dict]),
        }
    ]),
})

project_schema = project_schema_v1_0

SCHEMAS = {
    '1.0': project_schema_v1_0,
}


def detect_version(project: dict) -> Schema:
    if '_version' not in project:
        raise KeyError("_version is a required key")

    version = str(project['_version'])

    if version not in SCHEMAS:
        raise KeyError("_version is not valid: '{}'".format(version))

    return SCHEMAS[version]


Callback = tp.Callable[[], tp.Any]
Transform = tp.Callable[[tp.Any], tp.Any]


class Project:
    FlagList = tp.List[tp.Dict[str, tp.Any]]
    instance = None

    def __init__(self):
        self.project_data = None

    def load(self, project_file: tp.Union[str, Path]):
        if not isinstance(project_file, Path):
            project_file = Path(project_file)

        if project_file.is_dir():
            project_file = project_file / 'project.yml'

        project_file = project_file.resolve()

        with open(str(project_file), 'r') as fp:
            yaml = safe_load(fp)
            schema = detect_version(yaml)
            self.project_data = schema.validate(yaml)

    @classmethod
    def default(cls, key: str, default: tp.Optional[tp.Any] = None,
                transform: tp.Optional[Transform] = None) -> Callback:
        """
        Generate a default method for a click argument.

        This is used to override default cli arguments from project files, while
        still retaining the ability to override the values on the command line.

        :param key: The project configuration key
        :param default: The default value the argument should have if not in project
        :return: The generated default function.
        """
        # We need to access the data on the singleton
        self = cls.get_instance()

        def _default() -> tp.Any:
            if not self.enabled:
                return default

            if key not in self.project_data:
                return default

            data = self.project_data[key]

            # Do any data transformations that need to occur to actually
            # use the data.
            if isinstance(data, Path):
                data = str(data)
            if callable(transform):
                data = transform(data)

            return data

        return _default

    @classmethod
    def get_instance(cls):
        if not Project.instance:
            Project.instance = cls()
        return Project.instance

    @property
    def enabled(self):
        return self.project_data is not None

    def template_environment(self) -> Environment:
        return Environment()

    @property
    def base(self) -> Path:
        base = self.project_data['base']  #: Path
        base = base.expanduser()

        if not base.exists():
            base.mkdir(parents=True, exist_ok=True)
        return base

    @property
    def flags(self) -> FlagList:
        if not self.enabled or 'flags' not in self.project_data:
            return []
        return self.project_data['flags']

    def flag(self, team: models.Team) -> FlagList:
        if not self.enabled or 'flags' not in self.project_data:
            return []

        env = self.template_environment()
        flags = []

        for item in self.project_data['flags']:
            flag = deepcopy(item)
            tmpl = env.from_string(flag['name'])
            flag['name'] = tmpl.render(num=team.number)
            flags.append(flag)
        return flags

    def post(self, service: models.Service) -> tp.List[dict]:
        """
        Get the post pwn configuration for a given service.

        :param service: The service we are attempting to pwn.
        :return: The configuration for that service.
        """
        for service_data in self.project_data['post']:
            if service.service_name == service_data['service']:
                return service_data['commands']
        return []

    def connect_database(self):
        conf = Config.get_instance()
        db_path = conf.database(str(self.base))
        models.initialize(db_path)


@click.group()
def project():
    pass


@project.command()
@click.option('-b', '--base', required=True, prompt=True, type=click.Path())
@click.option('-n', '--name', required=True, prompt=True, type=click.STRING)
@click.option('-r', '--results', default=None, type=click.Path())
@click.option('-s', '--services', default=None, type=click.Path())
@click.option('-t', '--teams', default=None, type=click.Path())
def init(base, name, results, services, teams):
    utils.report_status("Creating project file at {}".format(base))
    base = Path(base).expanduser()

    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    base = base.resolve()

    data = {
        '_version': '1.0',
        'base': str(base),
        'project': name,
    }

    if results:
        data['results'] = results
    if services:
        data['services'] = services
    if teams:
        data['teams'] = teams

    with open(str(base / 'project.yml'), 'w') as fp:
        yaml.dump(data, fp, default_flow_style=False)
    utils.report_success("Project created")


@project.command()
@click.argument('path', type=click.Path())
def env(path):
    click.echo('export SLURPER_PROJECT={};'.format(path))
    click.echo('export unslurp() { unset SLURPER_PROJECT; unset -f unslurp; };')
    click.echo('echo "Set {} as current project. Run \'unslurp\' to unset";'.format(path))


def _default_creds():  # pragma: no cover
    models.CredentialBag.create(username='root', password='cdc')
    models.CredentialBag.create(username='toor', password='cdc')
    models.CredentialBag.create(username='cdc', password='cdc')

    # Very-open SSH
    models.CredentialBag.create(username='icanhasshell', password='cdc')
    models.CredentialBag.create(username='iamgroot', password='cdc')
    models.CredentialBag.create(username='chris', password='cdc')


@project.command()
def create_db():  # pragma: no cover
    """
    Create the database and add default credentials.
    """
    p = Project.get_instance()
    p.connect_database()
    models.create()
    _default_creds()


@project.command()
def clear_db():  # pragma: no cover
    """
    Remove all entries from the database and re-create default credentials.
    """
    p = Project.get_instance()
    p.connect_database()
    models.delete()
    _default_creds()
