import pytest
from click.testing import CliRunner

from flag_slurper.cli import cli
from flag_slurper.project import Project


@pytest.fixture
def pwn_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/pwn-test
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return str(tmpdir.join('project.yml'))


def test_autopwn_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'autopwn', 'results'])
    assert result.exit_code == 4
    assert result.output == "[!] AutoPWN commands require an active project\n"
