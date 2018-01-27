from typing import Dict


class Credential:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.works = set()
        self.rejected = set()

    def mark_works(self, team: int):
        self.works.add(team)
        self.rejected.remove(team)

    def mark_rejected(self, team: int):
        self.rejected.add(team)
        self.works.remove(team)
        return team in self.works

    def __eq__(self, other):
        return self.username == other.username and self.password == other.password

    def __ne__(self, other):
        return not self.__eq__(other)

    def __key(self):
        return self.username, self.password

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return "{}:{}".format(self.username, self.password)

    def __repr__(self):
        return "<Credential {}>".format(self.__str__())


class CredentialBag:
    instance = None

    def __init__(self):
        self.creds = {
            'root': {Credential('root', 'cdc')},
            'cdc': {Credential('cdc', 'cdc')},
        }

    @staticmethod
    def get_instance():
        if not CredentialBag.instance:
            return CredentialBag()
        return CredentialBag.instance

    def add_credential(self, cred: Credential):
        self.creds[cred.username].add(cred)

    def credentials(self):
        for creds in self.creds.values():
            for cred in creds:
                yield cred
