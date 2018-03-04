from pathlib import Path

from schema import Schema, Use, Optional

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


def detect_version(schema: dict) -> Schema:
    if '_version' not in schema:
        raise KeyError("_version is a required key")

    version = str(schema['_version'])

    if version not in SCHEMAS:
        raise KeyError("_version is not valid: '{}'".format(version))

    return SCHEMAS[version]
