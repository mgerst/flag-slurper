import pytest

from flag_slurper.config import Config


@pytest.fixture
def config():
    conf = Config.load(noflagrc=True)
    return conf
