import pytest
from click.testing import CliRunner

from flag_slurper.autolib.models import Service, Team
from flag_slurper.cli import cli
from flag_slurper.conf.project import Project


@pytest.fixture
def services_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/flag-test
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return str(tmpdir.join('project.yml'))


def test_services_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'services', 'ls'])
    assert result.exit_code == 4
    assert result.output == '[!] service commands require an active project\n'


def test_list_services(service, services_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', services_project, 'services', 'ls'])
    assert result.exit_code == 0
    assert service.service_name in result.output


def test_list_service_team(service, services_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', services_project, 'services', 'ls', '-t', service.team.number])
    assert result.exit_code == 0
    assert service.service_name in result.output


def test_list_service_excluded_team(service, services_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', services_project, 'services', 'ls', '-t', '3'])
    assert result.exit_code == 0
    assert service.service_name not in result.output


def test_add_service(runner, team, services_project):
    before = Service.select().count()
    result = runner(services_project, 'services', 'add', '100', 'WWW HTTP', '-p', '80', '-u', 'www.team1.isucdc.com',
                    '-t', str(team.number))
    assert result.exit_code == 0
    assert result.output == '[+] Service added\n'
    assert Service.select().count() - before == 1


def test_mass_add_service(runner, team, services_project):
    before = Service.select().count()
    result = runner(services_project, 'services', 'mass-add', 'WWW HTTP', '-p', '80', '-u', 'www.team{num}.isucdc.com')
    assert result.exit_code == 0
    assert result.output == '[+] Mass added service WWW HTTP\n'
    assert Service.select().count() - before == Team.select().count()
    service = Service.select().where(Service.team == team, Service.service_name == 'WWW HTTP').get()
    assert service.service_url == f'www.team{team.number}.isucdc.com'


def test_rm_service(service, services_project):
    runner = CliRunner()
    result = runner.invoke(cli, ['-p', services_project, 'services', 'rm', str(service.id)])
    assert result.exit_code == 0
    assert 'Service removed.' in result.output
    assert Service.select().where(Service.id == service.id).count() == 0


def test_edit_service(runner, service, services_project):
    result = runner(services_project, 'services', 'edit', str(service.id), '-u', '192.168.10.12')
    assert result.exit_code == 0
    assert result.output == f'[+] Updated service {service.id}\n'
    assert Service.get_by_id(service.id).service_url == '192.168.10.12'
