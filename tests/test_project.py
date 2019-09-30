import pytest
import yaml
from click.testing import CliRunner

from flag_slurper.cli import cli
from flag_slurper.conf import Project


@pytest.yield_fixture(scope='function', autouse=True)
def project_manage():
    """
    Clear out the Project singleton after each use.
    """
    yield
    Project.instance = None


class TestCli:
    def test_project_init(self, tmpdir):
        runner = CliRunner()
        result = runner.invoke(cli, ['project', 'init', '-n', 'test', '-b', str(tmpdir)])
        assert result.exit_code == 0
        assert 'Project created' in result.output

    def test_project_created(self, tmpdir):
        runner = CliRunner()
        result = runner.invoke(cli, ['project', 'init', '-n', 'test', '-b', str(tmpdir)])
        assert result.exit_code == 0

        expected = {
            '_version': '1.0',
            'base': str(tmpdir),
            'project': 'test',
        }

        project_file = tmpdir.join('project.yml').read()
        data = yaml.safe_load(project_file)
        assert expected == data

    def test_project_subdir_create(self, tmpdir):
        assert not tmpdir.join('sub').exists()
        runner = CliRunner()
        result = runner.invoke(cli, ['project', 'init', '-n', 'test', '-b', str(tmpdir) + "/sub"])
        assert result.exit_code == 0

        assert tmpdir.join('sub').join('project.yml').exists()

    def test_project_create_with_options(self, tmpdir):
        runner = CliRunner()
        result = runner.invoke(cli,
                               ['project', 'init', '-n', 'test', '-b', str(tmpdir), '-t', 't.yml', '-s', 's.yml', '-r',
                                'r.yml'])
        assert result.exit_code == 0

        expected = {
            '_version': '1.0',
            'base': str(tmpdir),
            'project': 'test',
            'teams': 't.yml',
            'services': 's.yml',
            'results': 'r.yml',
        }

        project_file = tmpdir.join('project.yml').read()
        data = yaml.safe_load(project_file)
        assert expected == data

    def test_project_env(self, basic_project):
        base = basic_project.base
        runner = CliRunner()
        result = runner.invoke(cli, ['project', 'env', str(base)])
        assert result.exit_code == 0
        assert 'export SLURPER_PROJECT={}'.format(base) in result.output
        assert 'export unslurp' in result.output
        assert 'Set {} as current project.'.format(base) in result.output
