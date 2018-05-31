import pytest

from flag_slurper.autolib.utils import limited_credentials


@pytest.fixture
def bags(bag, sudobag):
    bag.save()
    sudobag.save()
    yield [bag, sudobag]
    bag.delete().execute()
    sudobag.delete().execute()


def test_limit_root(bags):
    creds = limited_credentials(['root'])
    assert len(creds) == 1
    assert creds[0] == bags[0]


def test_no_limit(bags):
    creds = limited_credentials(None)
    assert len(creds) == 2


def test_excessive_limit(bags):
    creds = limited_credentials(['a'])
    assert len(creds) == 0
