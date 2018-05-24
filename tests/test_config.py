import shlex
from configparser import ConfigParser
from unittest import mock

from click.testing import CliRunner

from flag_slurper.autolib.governor import Governor
from flag_slurper.cli import cli
from flag_slurper.config import Config
from flag_slurper.models import User


def test_config_singleton(config):
    assert config is Config.get_instance()


def test_config_creation():
    Config.instance = None
    config = Config.get_instance()
    assert Config.instance is config


def test_config_load_extra(tmpdir):
    rc = tmpdir.join("flagrc.ini")
    rc.write("[iscore]\nurl=TESTURL\n")

    conf = Config.load(str(rc), noflagrc=True)
    assert conf['iscore']['url'] == 'TESTURL'


def test_config_cond_set(config):
    config.cond_set('iscore', 'api_token', 'TESTOKEN')
    assert config['iscore']['api_token'] == 'TESTOKEN'


def test_config_api_url(config):
    assert config.api_url == 'https://iscore.iseage.org/api/v1'


@mock.patch.object(Config, 'prompt_creds', lambda self: True)
def test_config_request_extras_token(config):
    config.cond_set('iscore', 'api_token', 'TESTOKEN')
    extras = config.request_extras()
    assert 'headers' in extras and 'Authorization' in extras['headers']
    assert extras['headers']['Authorization'] == 'Token TESTOKEN'


@mock.patch.object(Config, 'prompt_creds', lambda self: True)
def test_config_request_extras_creds(config):
    config.credentials = ('testuser', 'testpass')
    extras = config.request_extras()
    assert 'auth' in extras
    assert extras['auth'] == ('testuser', 'testpass')


def test_config_user(config):
    with mock.patch('flag_slurper.utils.get_user') as get_user:
        user = User({
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test',
            'is_superuser': True,
            'profile': {'is_red': False},
        })
        get_user.return_value = user
        result = config.user
        assert result == user


def test_config_prompt_token(config, capsys, mocker):
    mock = mocker.patch('flag_slurper.config.prompt')
    mock.return_value = "API_TOKEN"
    config.prompt_creds()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == "Enter your IScorE API Token (leave blank to use your credentials)\n"
    assert config['iscore']['api_token'] == 'API_TOKEN'


def test_config_prompt_creds(config, capsys, mocker):
    # API token, username, password
    prompt = mocker.patch('flag_slurper.config.prompt')
    prompt.side_effect = ['', 'test', 'pass']
    config.prompt_creds()
    captured = capsys.readouterr()
    assert captured.out == "Enter your IScorE API Token (leave blank to use your credentials)\nPlease login using your IScorE credentials\n"
    assert hasattr(config, 'credentials')
    assert config.credentials == ('test', 'pass')


def test_config_login(tmpdir):
    runner = CliRunner()
    args = shlex.split('config login -c {} -t abcdef'.format(tmpdir.join('flagrc')))
    result = runner.invoke(cli, args)
    assert result.exit_code == 0

    c = ConfigParser()
    c.read_file(tmpdir.join('flagrc').open('r'))
    assert 'iscore' in c and 'api_token' in c['iscore']
    assert c['iscore']['api_token'] == 'abcdef'


def test_config_governor(tmpdir):
    rc = tmpdir.join("flagrc.ini")
    rc.write("[autopwn]\ngovernor=yes\ndelay=6m\n")

    Config.load(str(rc), noflagrc=True)
    gov = Governor.get_instance()
    assert gov.enabled
    assert gov.delay == 6 * 60
