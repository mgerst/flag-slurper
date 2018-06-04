import string
import zipfile

import click
import pytest
import vcr
from click.testing import CliRunner
from hypothesis import given, assume
from hypothesis.strategies import text, composite, integers, from_regex

from flag_slurper import utils
from flag_slurper.models import User

# Run tests that might reach out to the real IScorE
EXTERNAL_TESTS = True


@pytest.mark.parametrize('remote,expected', [
    ('shell.team1', {'username': 'root', 'host': 'shell.team1', 'port': 22}),
    ('cdc@shell.team1', {'username': 'cdc', 'host': 'shell.team1', 'port': 22}),
    ('shell.team1:2222', {'username': 'root', 'host': 'shell.team1', 'port': 2222}),
    ('cdc@shell.team1:2222', {'username': 'cdc', 'host': 'shell.team1', 'port': 2222}),
])
def test_remote(remote, expected):
    user, host, port = utils.parse_remote(remote)
    assert user == expected['username']
    assert host == expected['host']
    assert port == expected['port']


@pytest.mark.parametrize('options,expected', [
    ({'template': '{i}. {info[name]}'}, "1. Test\nSelection: 1\n"),
    ({'template': '{i}. {info[name]}', 'title': 'Test Title'}, "Test Title\n1. Test\nSelection: 1\n"),
    ({'template': '{i}. {info[name]}', 'prompt': 'Which Flag'}, "1. Test\nWhich Flag: 1\n"),
    ({'template': '{i}. {info[name]}', 'title': 'Test Title', 'prompt': 'Which Flag'},
     "Test Title\n1. Test\nWhich Flag: 1\n"),
    ({'template': '{info[name]} ({i})'}, "Test (1)\nSelection: 1\n"),
])
def test_prompt_choice(options, expected):
    @click.command()
    def cmd():
        items = {1: {'name': 'Test'}}
        options['info'] = items
        choice = utils.prompt_choice(**options)
        assert choice == 1

    runner = CliRunner()
    result = runner.invoke(cmd, input='1\n')
    assert not result.exception
    assert result.output == expected


@pytest.mark.parametrize('method,input,expected', (
    (utils.report_success, 'It Works!', '[+] It Works!\n'),
    (utils.report_status, 'Status Message', '[-] Status Message\n'),
    (utils.report_warning, 'Warning Message', '[*] Warning Message\n'),
    (utils.report_error, 'Error Message', '[!] Error Message\n'),
))
def test_report_utils(method, input, expected):
    @click.command()
    def cmd():
        method(input)

    runner = CliRunner()
    result = runner.invoke(cmd)
    assert not result.exception
    assert result.output == expected


def test_team_map():
    teams = [
        {'number': 1, 'name': 'Test Team 1'},
        {'number': 3, 'name': 'Test Team 3'},
        {'number': 2, 'name': 'Test Team 2'},
    ]
    team_map = utils.get_team_map(teams)
    assert team_map[1] == teams[0]
    assert team_map[2] == teams[2]
    assert team_map[3] == teams[1]


def test_save_flags(tmpdir):
    flags = {
        1: {'filename': 'team_1_www_etc.flag', 'data': 'TESTDATA'},
    }
    utils.save_flags(flags, team=1, base_path=str(tmpdir))
    flag_zip = tmpdir.join("team_1_flags.zip")
    assert flag_zip.check()

    z = zipfile.ZipFile(str(flag_zip))
    contents = z.read('team_1_www_etc.flag')
    assert contents.decode('utf-8') == 'TESTDATA\n'


def test_save_flags_all_teams(tmpdir):
    flags = {
        1: {'filename': 'team_1_www_etc.flag', 'data': 'TEST1'},
        2: {'filename': 'team_2_www_etc.flag', 'data': 'TEST2'},
    }
    utils.save_flags(flags, base_path=str(tmpdir))
    flag_zip = tmpdir.join("all_team_flags.zip")
    assert flag_zip.check()

    z = zipfile.ZipFile(str(flag_zip))
    contents = z.read('team_1_www_etc.flag')
    assert contents.decode('utf-8') == 'TEST1\n'
    contents = z.read('team_2_www_etc.flag')
    assert contents.decode('utf-8') == 'TEST2\n'


USER_ADMIN = {
    'first_name': 'Test',
    'last_name': 'Admin',
    'username': 'admin',
    'is_superuser': True,
    'profile': {'is_red': True},
}

USER_RED = {
    'first_name': 'Test',
    'last_name': 'Red',
    'username': 'red',
    'is_superuser': False,
    'profile': {'is_red': True},
}

USER_BLUE = {
    'first_name': 'Test',
    'last_name': 'Red',
    'username': 'red',
    'is_superuser': False,
    'profile': {'is_red': False},
}


@pytest.mark.parametrize('user,expected', (
    (User(USER_ADMIN), 0),
    (User(USER_RED), 0),
    (User(USER_BLUE), 2),
))
def test_check_user(user, expected):
    @click.command()
    def cmd():
        utils.check_user(user)

    runner = CliRunner()
    result = runner.invoke(cmd)
    assert result.exit_code == expected


@pytest.mark.skipif(not EXTERNAL_TESTS, reason="External tests disabled")
@vcr.use_cassette('fixtures/servicestatus.yaml')
def test_get_service_status():
    services = utils.get_service_status()
    assert services[0]['service_name'] == 'Forum HTTP'


@pytest.mark.skipif(not EXTERNAL_TESTS, reason="External tests disabled")
@vcr.use_cassette('fixtures/teams.yaml')
def test_get_teams(config):
    teams = utils.get_teams()

    assert len(teams) == 20



@pytest.mark.parametrize('given,expected', (
    ('root', ('root', None)),
    ('root:cdc', ('root', 'cdc')),
))
def test_parse_creds(given, expected):
    result = utils.parse_creds(given)
    assert result == expected


@pytest.mark.parametrize('given,expected', (
    ('3', 3),
    ('5s', 5),
    ('10m', 10 * 60),
    ('3h', 3 * 60 * 60),
))
def test_parse_duration(given, expected):
    result = utils.parse_duration(given)
    assert result == expected


@pytest.mark.parametrize('given', (
    'abc',
    '30y',
    '2d',
))
def test_parse_duration_invalid(given):
    with pytest.raises(ValueError, match=r'Unable to parse \w+ as a duration$'):
        utils.parse_duration(given)


def test_parse_duration_empty():
    with pytest.raises(ValueError, match=r'Unable to parse empty duration'):
        utils.parse_duration('')


@given(from_regex(r'\A[0-9]+[smh]?\Z'))
def test_parse_duration_hyp(s):
    assume(len(s) > 0)
    assert utils.parse_duration(s) >= 0

