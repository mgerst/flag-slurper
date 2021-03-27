import pytest
from click.testing import CliRunner

from flag_slurper.autolib.models import Database
from flag_slurper.cli import cli
from flag_slurper.conf.project import Project


@pytest.fixture
def found_database(service):
    yield Database.create(id=1, type='mysql', version='0.1.2', username='foo', password='bar')


@pytest.fixture()
def dbs_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/flag-test
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return str(tmpdir.join('project.yml'))


def test_dbs_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'databases', 'ls'])
    assert result.exit_code == 4
    assert result.output == '[!] Database commands require an active project\n'
