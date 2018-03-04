import pytest

from flag_slurper.autolib import Service
from flag_slurper.autolib.credentials import Credential, FlagBag


@pytest.fixture
def service():
    return Service(1, 1, 'HTTP', 80, 'www.team1.isucdc.com', 1, 'Test Team', 1, 'UP', 0, 0, False)


def test_flagbag_add(service):
    bag = FlagBag()
    bag.add_flag(service, ('/root/team1_http_root.flag', 'ABCDEFG'))

    assert bag.flags[0].service == service
    assert bag.flags[0].contents[1] == 'ABCDEFG'
