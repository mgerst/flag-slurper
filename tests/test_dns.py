import pytest
from click.testing import CliRunner

from flag_slurper.autolib.models import DNSResult
from flag_slurper.cli import cli
from flag_slurper.project import Project


@pytest.fixture
def found_record(team):
    yield DNSResult.create(id=1, name='www', record='IN A 192.168.1.1', team=team)


@pytest.fixture()
def dns_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/flag-test
    flags: []
    """)
    p = Project.get_instance()
    project_file = str(tmpdir.join('project.yml'))
    p.load(project_file)
    return project_file


def test_dns_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'dns', 'ls'])
    assert result.exit_code == 4
    assert result.output == "[!] DNS commands require an active project\n"


def test_list_records(found_record, dns_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', dns_project, 'dns', 'ls'])
    assert result.exit_code == 0
    assert found_record.name in result.output
    assert found_record.record in result.output
