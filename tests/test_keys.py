import pytest

from flag_slurper.autolib.models import Key
from flag_slurper.conf import Project


@pytest.fixture
def shared_key(db):
    yield Key.create(id=1, username='cdc', contents='--- BEGIN OPENSSH PRIVATE KEY ---')


@pytest.fixture
def keys_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/flag-test
    flags:
      - service: WWW SSH
        type: blue
        location: /root
        name: team{{{{ num }}}}_www_root.flag
        search: yes
    """)
    project_path = str(tmpdir.join('project.yml'))
    p = Project.get_instance()
    p.load(project_path)
    return project_path


def test_keys_no_project(np_runner):
    p = Project.get_instance()
    p.project_data = None
    result = np_runner('keys', 'ls')
    assert result.exit_code == 4
    assert result.output == '[!] Key commands require an active project\n'


def test_list_keys(runner, keys_project, shared_key):
    result = runner(keys_project, 'keys', 'ls')
    assert result.exit_code == 0
    assert shared_key.username in result.output


def test_list_filter_by_team(runner, keys_project, shared_key):
    result = runner(keys_project, 'keys', 'ls', '-t', '5')
    assert result.exit_code == 1
    assert result.output == '[*] No keys found\n'


def test_list_filter_by_username_not_found(runner, keys_project, shared_key):
    result = runner(keys_project, 'keys', 'ls', '-u', 'non-existant')
    assert result.exit_code == 1
    assert result.output == '[*] No keys found\n'


def test_list_filter_by_username(runner, keys_project, shared_key):
    result = runner(keys_project, 'keys', 'ls', '-u', shared_key.username)
    assert result.exit_code == 0
    assert shared_key.username in result.output


def test_show_key(runner, shared_key, keys_project, mocker):
    edit = mocker.patch('flag_slurper.keys.click.edit')
    result = runner(keys_project, 'keys', 'show', str(shared_key.id))
    assert result.exit_code == 0
    assert edit.called
    assert shared_key.username in result.output


def test_get_key(runner, shared_key, keys_project, tmpdir):
    file = tmpdir.join('test.priv')
    result = runner(keys_project, 'keys', 'get', str(shared_key.id), str(file))
    assert result.exit_code == 0
    assert file.read() == shared_key.contents


def test_add_key(runner, keys_project, db, tmpdir):
    keyfile = tmpdir.join('keyfile')
    keyfile.write('TEST KEY')
    result = runner(keys_project, 'keys', 'add', str(keyfile), '-u', 'cdc')
    assert result.exit_code == 0
    assert '[+] Added key for cdc'


def test_add_key_for_team(runner, team, keys_project, tmpdir):
    keyfile = tmpdir.join('keyfile')
    keyfile.write('TEST KEY')
    result = runner(keys_project, 'keys', 'add', str(keyfile), '-u', 'cdc', '-t', str(team.id))
    assert result.exit_code == 0
    assert '[+] Added key for cdc'
    assert Key.select().order_by(Key.id.desc()).get().team.number == 1


def test_rm_key(runner, keys_project, shared_key):
    result = runner(keys_project, 'keys', 'rm', str(shared_key.id))
    assert result.exit_code == 0
    assert result.output == 'Key removed.\n'
    assert Key.select().where(Key.id == shared_key.id).count() == 0
