import pytest

from flag_slurper.autolib.models import CredentialBag, Credential


@pytest.fixture
def bag():
    return CredentialBag(username='root', password='cdc')


@pytest.fixture
def credential(bag, service):
    yield Credential(bag=bag, state=Credential.WORKS, service=service)


def test_cred_bag__str__(bag):
    assert bag.__str__() == "root:cdc"


def test_cred_bag__repr__(bag):
    assert bag.__repr__() == "<CredentialBag root:cdc>"


def test_cred__str__(credential):
    assert credential.__str__() == "root:cdc"


def test_cred__repr__(credential):
    assert credential.__repr__() == "<Credential root:cdc>"
