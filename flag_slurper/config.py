from configparser import ConfigParser
from pathlib import Path
from typing import Optional

ROOT = Path(__file__)


class Config(ConfigParser):
    instance = None

    @classmethod
    def load(cls, extra: Optional[str] = None):
        conf = cls()
        conffiles = [
            str(ROOT / 'default.ini'),
            str((Path('~') / '.flagrc').expanduser()),
        ]
        if extra:
            conffiles.append(extra)
        conf.read(conffiles)

        cls.instance = conf
        return conf

    @staticmethod
    def get_instance():
        if not Config.instance:
            Config.load()
        return Config.instance
