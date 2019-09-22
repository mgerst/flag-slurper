from functools import wraps

from . import Config, Project


def serialize(d: dict, config: Config, project: Project):
    d['extra_file'] = config.extra_file
    d['noflagrc'] = config.noflagrc
    if config['iscore']['api_token']:
        d['token'] = config['iscore']['api_token']
    if not config['iscore']['api_token'] and hasattr(config, 'credentials'):
        d['credentials'] = config.credentials
    d['project_file'] = project.project_file
    return d


def deserialize(d: dict):
    conf = Config.get_instance(extra=d['extra_file'], noflagrc=d['noflagrc'])
    if 'token' in d:
        conf['iscore']['api_token'] = d['token']
    elif 'credentials' in d:
        conf.credentials = d['credentials']

    project = Project.get_instance()
    project.load(d['project_file'])
