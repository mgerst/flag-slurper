from pathlib import Path
from typing import Any

import click
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


class Callback:
    """
    Descriptor that returns a click option callback for accessing project
    attributes.

    This is used when click parameters need to be read from the project
    file if not already specified.
    """

    def __init__(self, key):
        self.key = key

    def __get__(self, instance, owner):
        if not instance:
            instance = Project.get_instance()

        print("Setting up callback")

        def _callback(ctx: click.core.Context, param: click.core.Option, value: Any):
            if not instance.enabled:
                print("not enabled")
                return

            if self.key not in instance.project_data[self.key]:
                print("configured")
                set_value = None
            else:
                print("not configured")
                set_value = instance.project_data[self.key]

            if not value:
                print("value not given")
                ctx.params[param.name] = set_value

        return _callback

    def __set__(self, instance, value):
        if not instance:
            instance = Project.get_instance()
        instance.project_data[self.key] = value


class Project:
    instance = None

    base = Callback('base')
    teams = Callback('teams')
    services = Callback('services')
    results = Callback('results')

    def __init__(self):
        self.project_data = None

    def load(self, project_file: str):
        with open(project_file, 'r') as fp:
            yaml = safe_load(fp)
            schema = detect_version(yaml)
            self.project_data = schema.validate(yaml)

    @classmethod
    def get_instance(cls):
        if not Project.instance:
            Project.instance = cls()
        return Project.instance

    @property
    def enabled(self):
        return self.project_data is not None
