from typing import Tuple


class Credential:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.works = []
        self.rejected = []

    def mark_works(self, service):
        self.works.append(service)
        print(self.works)

    def mark_rejected(self, service):
        self.rejected.append(service)

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


class CredentialBag():
    def __init__(self):
        self.creds = {
            'root': {Credential('root', 'cdc')},
            'cdc': {Credential('cdc', 'cdc')},
        }

    def add_credential(self, cred: Credential):
        self.creds[cred.username].add(cred)

    def credentials(self):
        for creds in self.creds.values():
            for cred in creds:
                yield cred


credential_bag = CredentialBag()


class Flag:
    def __init__(self, team: int, service: 'Service', contents: Tuple[str]):
        self.team = team
        self.service = service
        self.contents = contents


class FlagBag:
    """
    Manages the flags found during exploitation.
    """
    def __init__(self):
        self.flags = []

    def add_flag(self, service: 'Service', contents: Tuple[str, str]):
        self.flags.append(Flag(service.team_number, service, contents))


flag_bag = FlagBag()
