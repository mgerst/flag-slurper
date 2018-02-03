from unittest import mock

import pytest
from click.testing import CliRunner

from flag_slurper.cli import cli, pass_conf
from flag_slurper.config import Config


def test_cli_usage():
    runner = CliRunner()
    result = runner.invoke(cli)
    assert "Usage: " in result.output
    assert result.exit_code == 0


def test_cli_version():
    @cli.command()
    def cmd():
        pass

    runner = CliRunner()
    result = runner.invoke(cli, ['cmd'])
    assert result.exit_code == 0
    assert result.output == "Flag Slurper v0.2\n"


def test_cli_pass_config():
    @cli.command()
    @pass_conf
    def cmd(conf):
        assert conf == Config.get_instance()

    runner = CliRunner()
    runner.invoke(cli, ['cmd'])


def test_plant_invalid_user():
    runner = CliRunner()
    result = runner.invoke(cli, ['plant'])
    assert result.exit_code == 1


@pytest.mark.skip('Mocks not working')
@mock.patch('flag_slurper.utils.check_user')
def test_plant(check_user):
    check_user.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ['plant'])
    assert check_user.called
    assert result.exit_code == 0
