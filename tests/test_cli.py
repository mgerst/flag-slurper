import pytest
import responses
from click.testing import CliRunner

from flag_slurper import __version__
from flag_slurper.cli import cli, pass_conf
from flag_slurper.config import Config
from flag_slurper.project import Project

from . import response_mocks as rm


@pytest.fixture
def dummy_cmd():
    @cli.command()
    def cmd():
        pass
    return cmd


def test_cli_usage():
    runner = CliRunner()
    result = runner.invoke(cli, ['-h'])
    assert "Usage: " in result.output
    assert result.exit_code == 0


def test_cli_bare_usage():
    runner = CliRunner()
    result = runner.invoke(cli)
    assert "Usage: " in result.output
    assert result.exit_code == 0


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert result.output == "flag-slurper, version {}\n".format(__version__)


def test_cli_pass_config():
    @cli.command()
    @pass_conf
    def cmd(conf):
        assert conf == Config.get_instance()

    runner = CliRunner()
    runner.invoke(cli, ['cmd'])


@responses.activate
def test_plant_invalid_user(mocker):
    prompt = mocker.patch('flag_slurper.config.prompt')
    prompt.return_value = "ABC"
    responses.add(responses.GET, 'https://iscore.iseage.org/api/v1/user/show.json', status=200, json=rm.BLUE_USER)
    runner = CliRunner()
    result = runner.invoke(cli, ['plant'])
    assert result.exit_code == 2


@responses.activate
def test_plant(mocker):
    prompt = mocker.patch('flag_slurper.config.prompt')
    prompt.side_effect = ['ABC', '']
    click = mocker.patch('flag_slurper.cli.click.prompt')
    click.return_value = 0
    responses.add(responses.GET, 'https://iscore.iseage.org/api/v1/user/show.json', status=200, json=rm.RED_USER)
    responses.add(responses.GET, 'https://iscore.iseage.org/api/v1/flags.json', status=200, json=rm.RED_FLAGS)

    runner = CliRunner()
    result = runner.invoke(cli, ['plant'])
    print(result.output)
    assert result.exit_code == 0
    expected_flag = 'Flag: {}'.format(rm.RED_FLAGS[0]['data'])
    assert expected_flag in result.output


@responses.activate
def test_plant_invalid(mocker):
    prompt = mocker.patch('flag_slurper.config.prompt')
    prompt.side_effect = ['ABC', '']
    click = mocker.patch('flag_slurper.cli.click.prompt')
    click.return_value = 101
    responses.add(responses.GET, 'https://iscore.iseage.org/api/v1/user/show.json', status=200, json=rm.RED_USER)
    responses.add(responses.GET, 'https://iscore.iseage.org/api/v1/flags.json', status=200, json=rm.RED_FLAGS)

    runner = CliRunner()
    result = runner.invoke(cli, ['plant'])
    assert result.exit_code == 1
    assert 'Invalid selection' in result.output


@responses.activate
def test_plant_as_admin(mocker):
    # TODO: We might be able to move this boilerplate into a fixture
    prompt = mocker.patch('flag_slurper.config.prompt')
    prompt.side_effect = ['ABC', '']
    click = mocker.patch('flag_slurper.cli.click.prompt')
    click.return_value = 0
    responses.add(responses.GET, 'https://iscore.iseage.org/api/v1/user/show.json', status=200, json=rm.ADMIN_USER)
    responses.add(responses.GET, 'https://iscore.iseage.org/api/v1/flags.json', status=200, json=rm.ADMIN_FLAGS)

    runner = CliRunner()
    result = runner.invoke(cli, ['plant'])
    assert result.exit_code == 0
    assert "0. WWW /etc (red)\n1. WWW /root (blue)" in result.output
    assert "Flag: ABCDE" in result.output


def test_cli_load_project(create_project):
    @cli.command()
    def cmd():
        p = Project.get_instance()
        assert p.project_data is not None

    tmpdir = create_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    """)
    runner = CliRunner()
    result = runner.invoke(cli, ['--project', str(tmpdir.join('project.yml')), 'cmd'])

    assert result.exit_code == 0


def test_cli_load_project_append_file(mocker, dummy_cmd, tmpdir):
    project = mocker.patch('flag_slurper.cli.Project')
    runner = CliRunner()
    runner.invoke(cli, ['-p', str(tmpdir), 'cmd'])
    assert project.load.called_with(str(tmpdir.join('project.yml')))


def test_cli_shell(mocker):
    prompt = mocker.patch('flag_slurper.config.prompt')
    prompt.side_effect = ['ABC', '']
    click = mocker.patch('flag_slurper.cli.click.prompt')
    click.return_value = 0
    code = mocker.patch('flag_slurper.cli.code.InteractiveConsole')

    runner = CliRunner()
    result = runner.invoke(cli, ['shell'])
    assert result.exit_code == 0
    assert code.called
