from flag_slurper.autolib.post import PostContext
from flag_slurper.autolib.protocols import pwn_smtp


def test_smtp_failure(mock, service):
    smtp = mock.patch('flag_slurper.autolib.protocols.SMTP.helo')
    smtp.helo = RuntimeError()
    message, success, _ = pwn_smtp('smtp.invalid', 25, service, [], None, PostContext())
    assert not success
    assert message == 'Error while detecting'


def test_smtp_non_relay(mock, service):
    smtp = mock.patch('flag_slurper.autolib.protocols.SMTP')
    message, success, _ = pwn_smtp(service.service_url, 25, service, [], None, PostContext())
    assert not success
    assert smtp.called
    assert message == 'Not an open-relay'


def test_smtp_success(mock, service):
    smtp = mock.patch('flag_slurper.autolib.protocols.SMTP')
    smtp.return_value.__enter__.return_value.docmd.return_value = (250, b'Ok')
    message, success, _ = pwn_smtp(service.service_url, 25, service, [], None, PostContext())
    assert success
    assert message == 'Open Relay detected'
