import pytest
import yaml
from click.testing import CliRunner
from schema import SchemaMissingKeyError, SchemaUnexpectedTypeError, SchemaError

from flag_slurper.cli import cli
from flag_slurper.project import project_schema, detect_version, project_schema_v1_0, Project


@pytest.yield_fixture(scope='function', autouse=True)
def project_manage():
    """
    Clear out the Project singleton after each use.
    """
    yield
    Project.instance = None


@pytest.fixture
def basic_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    return p


class TestProjectValidation:
    def test_schema_valid(self, make_project):
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

    def test_schema_without_version(self, make_project):
        with pytest.raises(SchemaMissingKeyError, match="Missing keys: '_version'"):
            project_schema.validate(make_project("""
            ---
            project: test
            base: ~/test
            results: results.yml
            teams: teams.yml
            services: services.yml
            """))

    def test_schema_missing_project(self, make_project):
        with pytest.raises(SchemaMissingKeyError, match="Missing keys: 'project'"):
            project_schema.validate(make_project("""
            ---
            _version: "1.0"
            base: ~/test
            results: results.yml
            teams: teams.yml
            services: services.yml
            """))

    def test_schema_missing_base(self, make_project):
        with pytest.raises(SchemaMissingKeyError, match="Missing keys: 'base'"):
            project_schema.validate(make_project("""
            ---
            _version: "1.0"
            project: test
            results: results.yml
            teams: teams.yml
            services: services.yml
            """))

    def test_project_schema_missing_results(self, make_project):
        project_schema.validate(make_project("""
        ---
        _version: "1.0"
        project: ISU2-18
        base: ~/cdcs/isu2-2018
        teams: teams.yml
        services: services.yml
        """))

    def test_schema_missing_teams(self, make_project):
        project_schema.validate(make_project("""
        ---
        _version: "1.0"
        project: ISU2-18
        base: ~/cdcs/isu2-2018
        results: results.yml
        services: services.yml
        """))

    def test_schema_missing_services(self, make_project):
        project_schema.validate(make_project("""
        ---
        _version: "1.0"
        project: ISU2-18
        base: ~/cdcs/isu2-2018
        results: results.yml
        teams: teams.yml
        """))

    def test_schema_empty_document(self, make_project):
        with pytest.raises(SchemaUnexpectedTypeError, match="None should be instance of 'dict'"):
            project_schema.validate(make_project(""))

    def test_schema_with_flags_empty(self, make_project):
        p = project_schema.validate(make_project("""
        ---
        _version: "1.0"
        project: ISU2-18
        base: ~/cdcs/isu2-2018
        flags: []
        """))
        assert 'flags' in p
        assert p['flags'] == []

    def test_schema_with_flags_populated(self, make_project):
        p = project_schema.validate(make_project("""
        ---
        _version: "1.0"
        project: ISU2-18
        base: ~/cdcs/isu2-2018
        flags:
          - service: Web HTTP
            type: blue
            location: /root
            name: team{{ num }}_www_root.flag
            search: yes
        """))
        assert p['flags'] == [{
            'service': 'Web HTTP',
            'type': 'blue',
            'location': '/root',
            'name': 'team{{ num }}_www_root.flag',
            'search': True,
        }]

    def test_schema_with_invalid_flags(self, make_project):
        with pytest.raises(SchemaError, match="Missing keys"):
            project_schema.validate(make_project("""
            ---
            _version: "1.0"
            project: ISU2-18
            base: ~/cdcs/isu2-2018
            flags:
             - {}
            """))

    def test_schema_with_multiple_flags(self, make_project):
        p = project_schema.validate(make_project("""
        ---
        _version: "1.0"
        project: ISU2-18
        base: ~/cdcs/isu2-2018
        flags:
          - service: Web SSH
            type: blue
            location: /root
            name: team{{ num }}_www_root.flag'
            search: yes
          - service: Shell SSH
            type: blue
            location: /root
            name: team{{ num }}_shell_root.flag
            search: no
        """))
        assert len(p['flags']) == 2


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

    assert project.project_data is not None


def test_load_project_directory(create_project):
    tmpdir = create_project("""
    ---
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    """)

    project = Project.get_instance()
    project.load(str(tmpdir))
    assert project.project_data is not None


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


def test_project_default_empty(basic_project):
    p = basic_project
    default = p.default('results')
    assert default() is None


def test_project_default_given(basic_project):
    p = basic_project
    default = p.default('results', 'res.yml')
    assert default() == 'res.yml'


def test_project_default_from_project(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    results: cool.yml
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))
    default = p.default('results')
    assert default() == "cool.yml"


def test_project_default_transform(basic_project):
    p = basic_project
    default = p.default('_version', transform=lambda x: round(float(x)))
    assert default() == 1


def test_project_default_enabled():
    p = Project.get_instance()
    assert p.enabled is False

    default = p.default('test', 'def')
    assert default() == 'def'


def test_project_create_base(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))

    assert not tmpdir.join('isu2-18').exists()
    base = p.base
    assert tmpdir.join('isu2-18').exists()
    assert str(base) == str(tmpdir.join('isu2-18'))


def test_project_flags(create_project):
    tmpdir = create_project("""
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    flags:
      - service: Web HTTP
        type: blue
        location: /root
        name: team{{{{ num }}}}_www_root.flag
        search: yes
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))

    assert p.flags == [
        {
            'service': 'Web HTTP',
            'type': 'blue',
            'location': '/root',
            'name': 'team{{ num }}_www_root.flag',
            'search': True,
        }
    ]


def test_project_flag_single(create_project, team):
    tmpdir = create_project("""
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    flags:
      - service: Web HTTP
        type: blue
        location: /root
        name: team{{{{ num }}}}_www_root.flag
        search: yes
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))

    flags = p.flag(team)
    assert flags == [
        {
            'service': 'Web HTTP',
            'type': 'blue',
            'location': '/root',
            'name': 'team1_www_root.flag',
            'search': True,
        }
    ]


def test_project_flags_disabled():
    p = Project.get_instance()
    assert not p.enabled
    assert p.flags == []


def test_project_flag_disabled():
    p = Project.get_instance()
    assert not p.enabled
    assert p.flag(1) == []


def test_project_without_flags(basic_project):
    assert basic_project.flags == []


def test_project_without_flag(basic_project):
    assert basic_project.flag(1) == []


def test_project_without_post(basic_project, service):
    assert basic_project.post(service) == []

def test_project_post_command(create_project, service):
    tmpdir = create_project("""
    _version: "1.0"
    project: ISU2-18
    base: {dir}/isu2-18
    post:
      - service: WWW HTTP
        commands:
          - ssh_exfil:
              files:
                - /etc/testfile
          
    """)
    p = Project.get_instance()
    p.load(str(tmpdir.join('project.yml')))

    service_data = p.post(service)
    assert service_data == [
        {
            'ssh_exfil': {
                'files': [
                    '/etc/testfile',
                ],
            },
        },
    ]


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
