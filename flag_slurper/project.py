from pathlib import Path

import click
import yaml

from flag_slurper.conf.project import Project
from . import utils
from .autolib import models


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
