import pickle
from dataclasses import dataclass


@dataclass
class PwnContext:
    """
    All context needed for an autopwn process. Largely consists
    """
    project: object
    config: object

    def serialize(self):
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, serialized):
        return pickle.loads(serialized)
