import pytest
from schema import SchemaMissingKeyError, SchemaUnexpectedTypeError

from flag_slurper.project import project_schema, detect_version, project_schema_v1_0, Project


@pytest.yield_fixture(scope='function', autouse=True)
def project_manage():
    """
    Clear out the Project singleton after each use.
    """
    yield
    Project.instance = None


def test_project_schema_valid(make_project):
    result = project_schema.validate(make_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: ~/cdcs/isu2-2018
    results: results.yml
    teams: teams.yml
    services: services.yml
    """))

    assert result
    assert isinstance(result, dict)
    assert result['_version'] == "1.0"


def test_project_schema_without_version(make_project):
    with pytest.raises(SchemaMissingKeyError, match="Missing keys: '_version'"):
        project_schema.validate(make_project("""
        ---
        project: test
        base: ~/test
        results: results.yml
        teams: teams.yml
        services: services.yml
        """))


def test_project_schema_missing_project(make_project):
    with pytest.raises(SchemaMissingKeyError, match="Missing keys: 'project'"):
        project_schema.validate(make_project("""
        ---
        _version: "1.0"
        base: ~/test
        results: results.yml
        teams: teams.yml
        services: services.yml
        """))


def test_project_schema_missing_base(make_project):
    with pytest.raises(SchemaMissingKeyError, match="Missing keys: 'base'"):
        project_schema.validate(make_project("""
        ---
        _version: "1.0"
        project: test
        results: results.yml
        teams: teams.yml
        services: services.yml
        """))


def test_project_schema_missing_results(make_project):
    project_schema.validate(make_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: ~/cdcs/isu2-2018
    teams: teams.yml
    services: services.yml
    """))


def test_project_schema_missing_teams(make_project):
    project_schema.validate(make_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: ~/cdcs/isu2-2018
    results: results.yml
    services: services.yml
    """))


def test_project_schema_missing_services(make_project):
    project_schema.validate(make_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: ~/cdcs/isu2-2018
    results: results.yml
    teams: teams.yml
    """))


def test_project_schema_empty_document(make_project):
    with pytest.raises(SchemaUnexpectedTypeError, match="None should be instance of 'dict'"):
        project_schema.validate(make_project(""))


def test_project_detect_schema(make_project):
    project = make_project("""
    ---
    _version: 1.0
    """)

    schema = detect_version(project)
    assert schema == project_schema_v1_0


def test_project_detect_invalid_schema(make_project):
    project = make_project("""
    ---
    _version: 0.1
    """)

    with pytest.raises(KeyError, match="_version is not valid: '0.1'"):
        detect_version(project)


def test_project_detect_schema_missing_version(make_project):
    project = make_project("""
    ---
    {}
    """)

    with pytest.raises(KeyError, match="_version is a required key"):
        detect_version(project)


def test_project_singleton():
    project = Project.get_instance()
    assert project is Project.get_instance()


def test_load_project(create_project):
    tmpdir = create_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    """)

    project = Project.get_instance()
    project.load(str(tmpdir.join('project.yml')))

    assert project._project_data is not None


def test_project_disabled():
    p = Project.get_instance()
    assert not p.enabled


def test_project_enabled(create_project):
    tmpdir = create_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    """)

    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    assert p.enabled
