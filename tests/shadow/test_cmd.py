import pytest

from flag_slurper.conf.project import Project


@pytest.fixture()
def shadow_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: Flag Slurper Test
    base: {dir}/shadow-test
    flags: []
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return str(tmpdir.join('project.yml'))


def assert_none_found(result):
    assert result.output == "[*] No shadow entries found\n"
    assert result.exit_code == 1


def test_shadow_no_project(np_runner):
    result = np_runner('shadow', 'ls')
    assert result.exit_code == 4
    assert result.output == "[!] Shadow commands require an active project\n"


def test_list_shadow_empty(runner, shadow_project):
    result = runner(shadow_project, 'shadow', 'ls')
    assert_none_found(result)


def test_list_shadow(runner, shadow_project, shadow):
    result = runner(shadow_project, 'shadow', 'ls')
    assert result.exit_code == 0
    assert 'root' in result.output


def test_list_shadow_team(runner, shadow_project, shadow):
    result = runner(shadow_project, 'shadow', 'ls', '-t', '100')
    assert_none_found(result)


def test_list_shadow_service(runner, shadow_project, shadow):
    result = runner(shadow_project, 'shadow', 'ls', '-s', 'FOOBAR')
    assert_none_found(result)


def test_list_shadow_username(runner, shadow_project, shadow):
    result = runner(shadow_project, 'shadow', 'ls', '-u', 'nonexistant')
    assert_none_found(result)
