import pytest

from flag_slurper.autolib import Service


@pytest.fixture
def service():
    return Service(1, 1, 'HTTP', 80, 'www.team1.isucdc.com', 1, 'Test Team', 1, 'UP', 0, 0, False)


@pytest.fixture
def invalid_service():
    return Service(1, 1, 'INVALID', 10391, 'www.team1.isucdc.com', 1, 'Test Team', 1, 'UP', 0, 0, False)
