import pytest
from click.testing import CliRunner

from flag_slurper.autolib.models import SSHKey
from flag_slurper.cli import cli
from flag_slurper.project import Project


@pytest.fixture
def active_key(db):
    yield SSHKey.create(id=1, name='Active Key', active=True, data='ssh-rsa ABC')


@pytest.fixture
def keys_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/keys-test
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return str(tmpdir.join('project.yml'))


def test_keys_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'keys', 'ls'])
    assert result.exit_code == 4
    assert result.output == '[!] SSH Key commands require an active project\n'


def test_list_keys(active_key, keys_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', keys_project, 'keys', 'ls'])
    assert result.exit_code == 0
    assert 'Active Key' in result.output


def test_list_keys_by_name(active_key, keys_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', keys_project, 'keys', 'ls', '-n', 'ABC'])
    assert result.exit_code == 1
    assert result.output == '[*] No keys found\n'
