import pytest

from flag_slurper.autolib.models import Credential, CredentialBag

@pytest.fixture
def bag():
    return CredentialBag(username='root', password='cdc')


@pytest.fixture
def sudobag():
    return CredentialBag(username='cdc', password='cdc')


@pytest.fixture
def credential(bag, service):
    yield Credential(bag=bag, state=Credential.WORKS, service=service)


@pytest.fixture
def sudocred(sudobag, service):
    yield Credential(bag=sudobag, state=Credential.WORKS, service=service, sudo=True)
