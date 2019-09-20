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


def test_autopwn_pwn_limit_team(pwn_project, mocker, service):
    runner = CliRunner()
    pwn_service = mocker.patch('flag_slurper.autopwn._pwn_service')
    result = runner.invoke(cli, ['autopwn', 'pwn', '-t', service.team.number])
    assert result.exit_code == 0
    pwn_service.assert_called_with((), service)


def test_autopwn_pwn_limit_service(pwn_project, mocker):
    runner = CliRunner()
    pwn_service = mocker.patch('flag_slurper.autopwn._pwn_service')
    result = runner.invoke(cli, ['autopwn', 'pwn', '-s', 'non-existant service'])
    assert result.exit_code == 0
    pwn_service.assert_not_called()


def test_autopwn_pwn_random(pwn_project, mocker):
    runner = CliRunner()
    mocker.patch('flag_slurper.autopwn._pwn_service')
    from flag_slurper.autopwn import fn
    random = mocker.spy(fn, 'Random')
    result = runner.invoke(cli, ['autopwn', 'pwn', '-r'])
    assert result.exit_code == 0
    random.assert_called()
