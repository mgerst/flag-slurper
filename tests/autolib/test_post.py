from io import BytesIO, StringIO
from textwrap import dedent

import pytest
from schema import SchemaError, Optional

from flag_slurper.autolib import post, models

SHADOW_FILE = dedent("""
root:$6$tLFrPk73$3dvrIViNCOl8F4ib63vWlliwqklJofCqIv0.Oc5.rTEKr4KOU5jzYNhoRf9E6.6xSjfLd66UpCThA0Vk4ntOu/:18349:0:99999:7:::
daemon:*:17959:0:99999:7:::
bin:*:17959:0:99999:7:::
sys:*:17959:0:99999:7:::
sync:*:17959:0:99999:7:::
games:*:17959:0:99999:7:::
man:*:17959:0:99999:7:::
lp:*:17959:0:99999:7:::
mail:*:17959:0:99999:7:::
news:*:17959:0:99999:7:::
uucp:*:17959:0:99999:7:::
proxy:*:17959:0:99999:7:::
www-data:*:17959:0:99999:7:::
backup:*:17959:0:99999:7:::
list:*:17959:0:99999:7:::
irc:*:17959:0:99999:7:::
gnats:*:17959:0:99999:7:::
nobody:*:17959:0:99999:7:::
libuuid:!:17959:0:99999:7:::
syslog:*:17959:0:99999:7:::
messagebus:*:18320:0:99999:7:::
landscape:*:18320:0:99999:7:::
cdc:$6$Jo7WSjVM$LgeIDfPuWg/mKtHJPtYonwj16KlinOFb17bKe52/WxcqcSZVQETx7rz4aKO5Nxnf2wauChXB87CYqzVpTmyJb0:18320:0:99999:7:::
sshd:*:18320:0:99999:7:::
wildfly:!:18320:0:99999:7:::
chris:!:18322:0:99999:7:::
bob:!:18322:0:99999:7:::
alice:!:18322:0:99999:7:::
telnetd:*:18323:0:99999:7:::
ntp:*:18349:0:99999:7:::
""").strip()


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
    pm.configure([{'test': {'foo': 'bar'}}])


def test_plugin_configure_invalid():
    pm = post.PluginRegistry()
    pm.register(TestPlugin)
    with pytest.raises(SchemaError):
        pm.configure([{'test': {'foo': False}}])


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


def test_plugin_non_configured():
    TestPlugin.schema = None
    plugin = TestPlugin()

    with pytest.raises(ValueError, match='The schema for test has not been configured'):
        plugin.configure({})


def test_plugin_non_configured_context():
    TestPlugin.context_schema = None
    plugin = TestPlugin()

    with pytest.raises(ValueError, match='The context_schema for test has not been configured'):
        plugin.run(None, None)


def test_registry_too_many_keys():
    registry = post.PluginRegistry()

    with pytest.raises(ValueError, match='Each commands entry should have exactly one key'):
        registry.configure([{'a': {}, 'b': {}}])


def test_registry_non_registered_plugin():
    registry = post.PluginRegistry()

    with pytest.raises(KeyError, match='Unknown plugin: foo'):
        registry.configure([{'foo': {}}])


def test_ssh_plugin_predicate_accepts(service):
    plugin = post.SSHFileExfil()
    service.service_port = 22
    assert plugin.predicate(service, post.PostContext())


def test_ssh_plugin_predicate_rejects(service):
    plugin = post.SSHFileExfil()
    assert not plugin.predicate(service, post.PostContext())


def test_ssh_plugin_run(service, mocker, sudobag, sudocred):
    sudocred.bag.save()
    sudocred.save()
    ssh = mocker.MagicMock()
    mocker.patch('flag_slurper.autolib.post.get_directory')

    validate = mocker.patch('flag_slurper.autolib.post.Schema.validate')
    validate.return_value = {}

    run_sudo = mocker.patch('flag_slurper.autolib.post.run_sudo')
    run_sudo.return_value = [StringIO(), BytesIO(b""), BytesIO()]

    ssh.exec_command.return_value = [StringIO(), BytesIO(b""), BytesIO()]
    context = post.PostContext(ssh=ssh, credentials=[sudocred.bag])

    plugin = post.SSHFileExfil()
    plugin.run(service, context)

    assert run_sudo.called
    assert ssh.exec_command.called


def test_shadow_plugin_predicate_accepts(service):
    plugin = post.ShadowExtractor()
    service.service_port = 22
    assert plugin.predicate(service, post.PostContext())


def test_shadow_plugin_predicate_rejects(service):
    plugin = post.ShadowExtractor()
    assert not plugin.predicate(service, post.PostContext())


def test_shadow_plugin_run(service, mocker):
    context = post.PostContext()
    shadow = models.File.create(service=service, path='/etc/shadow', contents=SHADOW_FILE)

    plugin = post.ShadowExtractor()
    plugin.run(service, context)

    assert models.ShadowEntry.select().count() == 2

    entry = models.ShadowEntry.select().first()
    assert entry.source == shadow
    assert entry.username == 'root'
    assert entry.hash == '$6$tLFrPk73$3dvrIViNCOl8F4ib63vWlliwqklJofCqIv0.Oc5.rTEKr4KOU5jzYNhoRf9E6.6xSjfLd66UpCThA0Vk4ntOu/'
