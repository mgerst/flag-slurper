import pytest
from click.testing import CliRunner

from flag_slurper.autolib.models import File
from flag_slurper.cli import cli
from flag_slurper.project import Project


@pytest.fixture
def found_file(service):
    yield File.create(id=1, path='/test/fun/file', contents='abcdef'.encode('utf-8'), mime_type='text/plain',
                      info='ASCII text',
                      service=service)


@pytest.fixture()
def files_project(create_project):
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
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return str(tmpdir.join('project.yml'))


def test_files_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'files', 'ls'])
    assert result.exit_code == 4
    assert result.output == "[!] File commands require an active project\n"


def test_list_files(found_file, files_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', files_project, 'files', 'ls'])
    assert result.exit_code == 0
    assert '/test/fun/file' in result.output
    assert 'ASCII text' in result.output


def test_list_files_team(found_file, files_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', files_project, 'files', 'ls', '-t', '100'])
    assert result.exit_code == 1
    assert result.output == "[*] No files found\n"


def test_list_files_by_service(found_file, files_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', files_project, 'files', 'ls', '-s', 'DNS'])
    assert result.exit_code == 1
    assert result.output == "[*] No files found\n"


def test_list_files_by_path(found_file, files_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', files_project, 'files', 'ls', '-n', 'fun'])
    assert result.exit_code == 0
    assert '/test/fun/file' in result.output


def test_show_file(found_file, mock, files_project):
    edit = mock.patch('flag_slurper.files.click.edit')
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', files_project, 'files', 'show', str(found_file.id)])
    assert result.exit_code == 0
    assert edit.called
    assert found_file.path in result.output
    assert found_file.mime_type in result.output
    assert found_file.info in result.output
    assert found_file.service.service_name in result.output


def test_get_file(found_file, tmpdir, files_project):
    file = tmpdir.join('testfile')
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', files_project, 'files', 'get', str(found_file.id), str(file)])
    assert result.exit_code == 0
    assert file.read() == found_file.contents.decode('utf-8')


def test_rm_file(found_file, files_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', files_project, 'files', 'rm', str(found_file.id)])
    assert result.exit_code == 0
    assert File.select().where(File.id == found_file.id).count() == 0
