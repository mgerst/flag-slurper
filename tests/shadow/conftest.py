import pytest

from flag_slurper.autolib.models import ShadowEntry, File


@pytest.fixture
def file(service):
    yield File.create(id=1, path='/etc/shadow', contents='root:foo'.encode('utf-8'), mime_types='text/plain',
                      info='ASCII text', service=service)


@pytest.fixture
def shadow(service, file):
    yield ShadowEntry.create(id=1, service=service, source=file, username='root', hash='foo')
