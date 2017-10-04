import click
from click.testing import CliRunner
import pytest

from flag_slurper import utils


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
