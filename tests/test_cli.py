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
    assert result.output == "Flag Slurper v0.1\n"


def test_cli_pass_config():
    @cli.command()
    @pass_conf
    def cmd(conf):
        assert conf == Config.get_instance()
