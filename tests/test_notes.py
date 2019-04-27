import pytest
from click.testing import CliRunner

from flag_slurper.autolib.models import CaptureNote
from flag_slurper.cli import cli
from flag_slurper.project import Project


@pytest.fixture
def capture_note(service, flag):
    yield CaptureNote.create(id=1, flag=flag, service=service, data='abcdef', location='/etc/team1_www_root.flag',
                             notes='abc'*20)


@pytest.fixture
def notes_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/flag-test
    flags:
        - service: WWW SSH
          type: blue
          location: /etc
          name: team{{{{ num }}}}_www_root.flag
          search: yes
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return str(tmpdir.join('project.yml'))


def test_notes_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'notes', 'ls'])
    assert result.exit_code == 4
    assert result.output == '[!] Capture note commands require an active project\n'


def test_list_notes(capture_note, notes_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', notes_project, 'notes', 'ls'])
    assert result.exit_code == 0
    assert capture_note.location, result.output
    assert capture_note.flag.name, result.output


def test_list_notes_team(capture_note, notes_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', notes_project, 'notes', 'ls', '-t', '1000'])
    assert result.exit_code == 1
    assert result.output == '[*] No capture notes found\n'


def test_list_notes_by_service(capture_note, notes_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', notes_project, 'notes', 'ls', '-s', 'ABCDEF'])
    assert result.exit_code == 1
    assert result.output == '[*] No capture notes found\n'


def test_show_note(capture_note, notes_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', notes_project, 'notes', 'show', str(capture_note.id)])
    assert result.exit_code == 0
    assert capture_note.location in result.output
    assert capture_note.data in result.output
    assert capture_note.notes in result.output

def test_show_note_not_found(capture_note, notes_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', notes_project, 'notes', 'show', str(1001)])
    assert result.exit_code == 1
    assert '[!] Capture note 1001 does not exist' in result.output
