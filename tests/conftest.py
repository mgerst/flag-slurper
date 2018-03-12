from textwrap import dedent

import pytest
from yaml import safe_load

from flag_slurper.config import Config


@pytest.fixture
def config():
    conf = Config.load(noflagrc=True)
    return conf


@pytest.fixture
def make_project():
    def _make(text):
        return safe_load(dedent(text).strip())

    return _make


@pytest.fixture
def create_project(tmpdir):
    def _make(text):
        p = tmpdir.join('project.yml')
        p.write(dedent(text.format(dir=tmpdir)).strip())

        return tmpdir
    return _make
