from pathlib import Path

from schema import Schema, Use, Optional
from yaml import safe_load

project_schema_v1_0 = Schema({
    '_version': Use(str, error='Must include _version'),
    'project': str,
    'base': Use(Path, error='base must be a path'),
    Optional('results'): Use(Path, error='results must be a path'),
    Optional('teams'): Use(Path, error='teams must be a path'),
    Optional('services'): Use(Path, error='services must be a path'),
})

project_schema = project_schema_v1_0

SCHEMAS = {
    '1.0': project_schema_v1_0,
}


def detect_version(project: dict) -> Schema:
    if '_version' not in project:
        raise KeyError("_version is a required key")

    version = str(project['_version'])

    if version not in SCHEMAS:
        raise KeyError("_version is not valid: '{}'".format(version))

    return SCHEMAS[version]


class Project:
    instance = None

    def __init__(self):
        self._project_data = None

    def load(self, project_file: str):
        with open(project_file, 'r') as fp:
            yaml = safe_load(fp)
            schema = detect_version(yaml)
            self._project_data = schema.validate(yaml)

    @classmethod
    def get_instance(cls):
        if not Project.instance:
            Project.instance = cls()
        return Project.instance
