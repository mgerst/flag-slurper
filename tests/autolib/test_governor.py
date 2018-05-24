from datetime import datetime, timedelta

from flag_slurper.autolib.governor import Governor


def test_governor_singleton():
    Governor.instance = None
    Governor.get_instance(True)
    gov = Governor.get_instance()
    assert gov.enabled
    assert gov.delay == 5 * 60
    assert gov.window == 30 * 60
    assert gov.times == 3


def test_governor_tracks(mock):
    Governor.instance = None
    gov = Governor.get_instance(True)
    sleep = mock.patch('flag_slurper.autolib.governor.time.sleep')
    gov.attempt('192.168.1.113')
    assert not sleep.called


def test_governor_filter():
    Governor.instance = None
    gov = Governor.get_instance(True)
    gov.limits['192.168.1.113'] = [datetime.now() - timedelta(minutes=3),
                                   datetime.now() - timedelta(minutes=29),
                                   datetime.now() - timedelta(minutes=1),
                                   datetime.now() - timedelta(minutes=35)]
    gov.filter('192.168.1.113')
    assert len(gov.limits['192.168.1.113']) == 3


def test_governor_limits(mock):
    Governor.instance = None
    gov = Governor.get_instance(True)
    gov.limits['192.168.1.113'] = [datetime.now() - timedelta(minutes=3),
                                   datetime.now() - timedelta(minutes=29),
                                   datetime.now() - timedelta(minutes=1),
                                   datetime.now() - timedelta(minutes=35)]
    sleep = mock.patch('flag_slurper.autolib.governor.time.sleep')
    gov.attempt('192.168.1.113')
    assert sleep.called


def test_governer_doesnt_limit_when_disabled(mock):
    Governor.instance = None
    gov = Governor.get_instance(False)
    gov.limits['192.168.1.113'] = [datetime.now() - timedelta(minutes=3),
                                   datetime.now() - timedelta(minutes=29),
                                   datetime.now() - timedelta(minutes=1),
                                   datetime.now() - timedelta(minutes=35)]
    sleep = mock.patch('flag_slurper.autolib.governor.time.sleep')
    gov.attempt('192.168.1.113')
    assert not sleep.called


def test_governor_resolve(mock):
    addrhost = mock.patch('flag_slurper.autolib.governor.socket.gethostbyname')
    addrhost.return_value = '192.168.1.113'
    ipaddr = Governor.resolve_url('example.com')
    assert addrhost.called_with('example.com')
    assert ipaddr == '192.168.1.113'
