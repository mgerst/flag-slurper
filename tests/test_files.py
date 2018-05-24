import pytest
from click.testing import CliRunner

from flag_slurper.autolib.models import File
from flag_slurper.cli import cli


@pytest.fixture
def found_file(service):
    yield File.create(id=1, path='/test/fun/file', contents='abcdef'.encode('utf-8'), mime_type='text/plain', info='ASCII text',
                      service=service)


def test_list_files(found_file):
    runner = CliRunner()
    result = runner.invoke(cli, ['files', 'ls'])
    assert result.exit_code == 0
    assert '/test/fun/file' in result.output
    assert 'ASCII text' in result.output


def test_list_files_team(found_file):
    runner = CliRunner()
    result = runner.invoke(cli, ['files', 'ls', '-t', '100'])
    assert result.exit_code == 1
    assert result.output == "[*] No files found for team 100\n"


def test_show_file(found_file, mock):
    edit = mock.patch('flag_slurper.files.click.edit')
    runner = CliRunner()
    result = runner.invoke(cli, ['files', 'show', str(found_file.id)])
    assert result.exit_code == 0
    assert edit.called
    assert found_file.path in result.output
    assert found_file.mime_type in result.output
    assert found_file.info in result.output
    assert found_file.service.service_name in result.output


def test_get_file(found_file, tmpdir):
    file = tmpdir.join('testfile')
    runner = CliRunner()
    result = runner.invoke(cli, ['files', 'get', str(found_file.id), str(file)])
    assert result.exit_code == 0
    assert file.read() == found_file.contents.decode('utf-8')


def test_rm_file(found_file):
    runner = CliRunner()
    result = runner.invoke(cli, ['files', 'rm', str(found_file.id)])
    assert result.exit_code == 0
    assert File.select().where(File.id == found_file.id).count() == 0
