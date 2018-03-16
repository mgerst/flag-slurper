import pytest

from flag_slurper.autolib.credentials import Credential, CredentialBag, FlagBag


@pytest.fixture
def cred():
    return Credential(username='user', password='pass')


def test_flagbag_add(service):
    bag = FlagBag()
    bag.add_flag(service, ('/root/team1_http_root.flag', 'ABCDEFG'))

    assert bag.flags[0].service == service
    assert bag.flags[0].contents[1] == 'ABCDEFG'


class TestCredential:
    def test__eq__(self, cred):
        cred2 = Credential(username='user', password='pass')
        assert cred == cred2

    def test__neq__(self, cred):
        cred2 = Credential(username='user2', password='pass2')
        assert cred != cred2

    def test__str__(self, cred):
        assert cred.__str__() == "user:pass"

    def test_mark_works(self, cred, service):
        cred.mark_works(service)
        assert service in cred.works
        assert service not in cred.rejected

    def test_mark_rejected(self, cred, service):
        cred.mark_rejected(service)
        assert service not in cred.works
        assert service in cred.rejected


class TestCredentialBag:
    def test_add_credential(self, cred):
        bag = CredentialBag()
        bag.add_credential(cred)
        assert cred.username in bag.creds
        assert cred in bag.creds[cred.username]

    def test_credentials(self):
        bag = CredentialBag()
        creds = sorted(list(bag.credentials()), key=lambda x: x.username)
        assert creds[0].username == 'cdc' and creds[0].password == 'cdc'
        assert creds[1].username == 'root' and creds[1].password == 'cdc'
