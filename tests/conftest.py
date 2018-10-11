from textwrap import dedent

import pytest
from peewee import SqliteDatabase, PostgresqlDatabase
from yaml import safe_load

from flag_slurper.autolib import models
from flag_slurper.config import Config

MODELS = [models.Service, models.Credential, models.CredentialBag, models.Team, models.Flag, models.CaptureNote,
          models.File, models.DNSResult]


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


@pytest.fixture
def db():
    test_db = PostgresqlDatabase('slurpertest')

    for model in MODELS:
        model.bind(test_db, bind_refs=False, bind_backrefs=False)

    test_db.create_tables(MODELS)
    with test_db.transaction() as txn:
        yield txn
        txn.rollback()


@pytest.fixture
def team(db):
    yield models.Team.create(id=1, name='CDC Team 1', number=1, domain='team1.isucdc.com')


@pytest.fixture
def service(team):
    yield models.Service.create(remote_id=1, service_id=1, service_name='WWW HTTP', service_port=80,
                                service_url='www.team1.isucdc.com', admin_status=None, high_target=0, low_target=0,
                                is_rand=False, team=team)


@pytest.fixture
def invalid_service(team):
    yield models.Service.create(remote_id=2, service_id=2, service_name='WWW Custom', service_port=10391,
                                service_url='www.team1.isucdc.com', admin_status=None, high_target=0, low_target=0,
                                is_rand=False, team=team)


@pytest.fixture
def flag(team):
    yield models.Flag.create(id=1, team=team, name='Test Team')
