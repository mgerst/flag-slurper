import shlex
from configparser import ConfigParser

from click.testing import CliRunner

from flag_slurper.cli import cli


def test_config_login(tmpdir):
    runner = CliRunner()
    args = shlex.split('config login -c {} -t abcdef'.format(tmpdir.join('flagrc')))
    result = runner.invoke(cli, args)
    assert result.exit_code == 0

    c = ConfigParser()
    c.read_file(tmpdir.join('flagrc').open('r'))
    assert 'iscore' in c and 'api_token' in c['iscore']
    assert c['iscore']['api_token'] == 'abcdef'
