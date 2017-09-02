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
