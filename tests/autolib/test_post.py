from io import BytesIO, StringIO

import pytest
from schema import SchemaError, Optional

from flag_slurper.autolib import post


def test_pos_ssh(mock, sudocred):
    """
    TODO This clearly needs to be a lot better.
    """
    ssh = mock.MagicMock()
    mock.patch('flag_slurper.autolib.post.get_directory')

    run_sudo = mock.patch('flag_slurper.autolib.post.run_sudo')
    run_sudo.return_value = [StringIO(), BytesIO(b""), BytesIO()]

    ssh.exec_command.return_value = [StringIO(), BytesIO(b""), BytesIO()]

    post.post_ssh(ssh, sudocred)

    assert run_sudo.called
    assert ssh.exec_command.called


class TestPlugin(post.PostPlugin):
    name = 'test'
    schema = {
        Optional('foo'): str,
    }
    context_schema = {}

    def run(self, service: post.Service, context: post.PostContext):
        super().run(service, context)

    def predicate(self, service: post.Service, context: post.PostContext):
        return True


def test_plugin_registered():
    pm = post.PluginRegistry()
    pm.register(TestPlugin)
    assert 'test' in pm.registry


def test_register_non_subclass():
    pm = post.PluginRegistry()
    with pytest.raises(ValueError, match='Plugins must extend PostPlugin'):
        pm.register(object)


def test_register_duplicate_plugin():
    pm = post.PluginRegistry()
    pm.register(TestPlugin)

    with pytest.raises(ValueError, match='Plugin already registered by this name: test'):
        pm.register(TestPlugin)


def test_context_validation_success():
    context = post.PostContext(foo='bar')
    context.validate({'foo': str})


def test_context_validation_error():
    context = post.PostContext(foo='bar')

    with pytest.raises(SchemaError):
        context.validate({'foo': int})


def test_plugin_configure():
    pm = post.PluginRegistry()
    pm.register(TestPlugin)
    pm.configure({'foo': 'bar'})


def test_plugin_configure_invalid():
    pm = post.PluginRegistry()
    pm.register(TestPlugin)
    with pytest.raises(SchemaError):
        pm.configure({'foo': False})


def test_plugin_run(service):
    class Test2(TestPlugin):
        context_schema = {}
        schema = {}
        name = 'test2'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.ran = True

        def run(self, service: post.Service, context: post.PostContext):
            super().run(service, context)
            self.ran = True
    pm = post.PluginRegistry()
    pm.register(Test2)
    pm.post(service, post.PostContext())
