import pickle
from dataclasses import dataclass

from . import Config, Project


@dataclass
class PwnProcContext:
    """
    All context needed for an autopwn process. Largely consists
    """
    project: Project
    config: Config

    def serialize(self):
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, serialized):
        return pickle.loads(serialized)
