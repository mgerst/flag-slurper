import pickle

import pytest

from flag_slurper.conf import PwnProcContext, Project


@pytest.yield_fixture(scope='function', autouse=True)
def project_manage():
    yield
    Project.instance = None


def test_project_serialized(basic_project, config):
    context = PwnProcContext(project=basic_project, config=config)
    serialized = context.serialize()
    deserialized = pickle.loads(serialized)
    assert deserialized.project.project_data == basic_project.project_data
    assert deserialized.config == config


def test_project_deserialize(basic_project, config):
    context = PwnProcContext(project=basic_project, config=config)
    serialized = pickle.dumps(context)
    deserialized = PwnProcContext.deserialize(serialized)
    assert deserialized.project.project_data == basic_project.project_data
    assert deserialized.config == config
