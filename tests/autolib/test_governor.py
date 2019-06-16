from datetime import datetime, timedelta
import socket

import pytest

from flag_slurper.autolib.governor import Governor


@pytest.fixture
def governor():
    Governor.instance = None
    return Governor.get_instance(True)


def test_governor_singleton():
    Governor.instance = None
    Governor.get_instance(True)
    gov = Governor.get_instance()
    assert gov.enabled
    assert gov.delay == 5 * 60
    assert gov.window == 30 * 60
    assert gov.times == 3


def test_governor_tracks(mock, governor):
    sleep = mock.patch('flag_slurper.autolib.governor.time.sleep')
    governor.attempt('192.168.1.113')
    assert not sleep.called


def test_governor_filter(governor):
    governor.limits['192.168.1.113'] = [datetime.now() - timedelta(minutes=3),
                                        datetime.now() - timedelta(minutes=29),
                                        datetime.now() - timedelta(minutes=1),
                                        datetime.now() - timedelta(minutes=35)]
    governor.filter('192.168.1.113')
    assert len(governor.limits['192.168.1.113']) == 3


def test_governor_limits(mock, governor):
    governor.limits['192.168.1.113'] = [datetime.now() - timedelta(minutes=3),
                                        datetime.now() - timedelta(minutes=29),
                                        datetime.now() - timedelta(minutes=1),
                                        datetime.now() - timedelta(minutes=35)]
    sleep = mock.patch('flag_slurper.autolib.governor.time.sleep')
    governor.attempt('192.168.1.113')
    assert sleep.called


def test_governer_doesnt_limit_when_disabled(mock):
    Governor.instance = None
    governor = Governor.get_instance(False)
    governor.limits['192.168.1.113'] = [datetime.now() - timedelta(minutes=3),
                                        datetime.now() - timedelta(minutes=29),
                                        datetime.now() - timedelta(minutes=1),
                                        datetime.now() - timedelta(minutes=35)]
    sleep = mock.patch('flag_slurper.autolib.governor.time.sleep')
    governor.attempt('192.168.1.113')
    assert not sleep.called


def test_governor_resolve(mock):
    addrhost = mock.patch('flag_slurper.autolib.governor.socket.gethostbyname')
    addrhost.return_value = '192.168.1.113'
    ipaddr = Governor.resolve_url('example.com')
    assert addrhost.called_with('example.com')
    assert ipaddr == '192.168.1.113'


def test_governor_resolve_failure(mock):
    addrhost = mock.patch('flag_slurper.autolib.governor.socket.gethostbyname')
    addrhost.side_effect = socket.gaierror()
    ipaddr = Governor.resolve_url('invalid.invalid')
    assert addrhost.called_with('invalid.invalid')
    assert ipaddr is None


def test_governor_does_not_limit_invalid_ip(mock, governor):
    governor.attempt(None)
    sleep = mock.patch('flag_slurper.autolib.governor.time.sleep')
    assert len(governor.limits) == 0
    assert not sleep.called
