from copy import deepcopy

import pytest

from flag_slurper.autolib.service import Service, Result, coerce_service, detect_service, pwn_service
from flag_slurper.autolib.protocols import PWN_FUNCS
from flag_slurper.project import Project


@pytest.fixture
def project(create_project):
    tmpdir = create_project("""
    ---
    _version: "1.0"
    project: IUS2-18
    base: {dir}/isu2-18
    """)
    project = Project.get_instance()
    project.load(str(tmpdir.join('project.yml')))
    yield project


class TestResult:
    def test_result_success__str__(self, service):
        result = Result(service, "test message", success=True, skipped=False)
        assert result.__str__() == "1/www.team1.isucdc.com:80/http Succeeded!  test message"

    def test_result_skipped__str__(self, service):
        result = Result(service, "test message", success=False, skipped=True)
        assert result.__str__() == "1/www.team1.isucdc.com:80/http Skipped pwn: test message"

    def test_result_error__str__(self, service):
        result = Result(service, "test message", success=False, skipped=False)
        assert result.__str__() == "1/www.team1.isucdc.com:80/http Failed pwn: test message"

    def test_result__eq__(self, service):
        result = Result(service, "test message", success=False, skipped=False)
        result2 = deepcopy(result)
        assert result == result2


def test_coerce_service():
    service = coerce_service({'id': 1, 'service_id': 1, 'service_name': 'Test SSH', 'service_port': 22,
                              'service_url': 'www.team1.isucdc.com', 'team_id': 1, 'team_name': 'CDC Team 1',
                              'team_number': 1, 'admin_status': None, 'high_target': 0, 'low_target': 0,
                              'is_rand': False})
    assert isinstance(service, Service)


def test_detect_service(service):
    data = detect_service(service)
    assert data[0] == 'http'
    assert data[1] == 'www.team1.isucdc.com'
    assert data[2] == 80


def test_detect_unknown_service(invalid_service):
    data = detect_service(invalid_service)
    assert data[0] == 'unknown'
    assert data[1] == 'www.team1.isucdc.com'
    assert data[2] == 10391


def test_pwn_invalid_service(invalid_service, project):
    res = pwn_service(invalid_service, None, None, project.post(invalid_service))
    assert not res.success
    assert res.skipped
    assert res.message == "Protocol not supported for autopwn"


def test_pwn_service(service, mocker, project):
    pwn_http = mocker.MagicMock()
    pwn_http.return_value = "service up", True, False

    PWN_FUNCS['http'] = pwn_http
    res = pwn_service(service, None, None, project.post(service))

    result = Result(service, "service up", success=True, skipped=False)
    assert result == res
    assert pwn_http.called


def test_pwn_flag_conf(service, mocker, project):
    pwn_http = mocker.MagicMock()
    pwn_http.return_value = "service up", True, False

    PWN_FUNCS['http'] = pwn_http
    res = pwn_service(service, [], None, project.post(service))

    result = Result(service, "service up", success=True, skipped=False)
    assert result == res
