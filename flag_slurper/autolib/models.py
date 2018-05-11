import click
import peewee
import playhouse.db_url

# We want to allow setting up the database connection from .flagrc
database_proxy = peewee.Proxy()
SUDO_FLAG = click.style('!', fg='red', bold=True)


def initialize(database_url: str):
    database = playhouse.db_url.connect(database_url)
    database_proxy.initialize(database)


class BaseModel(peewee.Model):
    class Meta:
        database = database_proxy


class CredentialBag(BaseModel):
    id = peewee.AutoField(primary_key=True)
    username = peewee.CharField(max_length=100)
    password = peewee.CharField(max_length=100)

    def __str__(self):
        return "{}:{}".format(self.username, self.password)

    def __repr__(self):
        return "<CredentialBag {}>".format(self.__str__())


class Team(BaseModel):
    id = peewee.IntegerField(primary_key=True)
    name = peewee.CharField(max_length=200)
    number = peewee.IntegerField()


class Service(BaseModel):
    id = peewee.AutoField(primary_key=True)
    remote_id = peewee.IntegerField(unique=True)
    service_id = peewee.IntegerField()
    service_name = peewee.CharField(max_length=100)
    service_port = peewee.SmallIntegerField()
    service_url = peewee.CharField(max_length=100)
    admin_status = peewee.CharField(choices=['DOWN', 'CAPPED'], null=True)
    high_target = peewee.IntegerField(null=True)
    low_target = peewee.IntegerField(null=True)
    is_rand = peewee.BooleanField(default=False)
    team = peewee.ForeignKeyField(Team, backref='services')


class Credential(BaseModel):
    WORKS = 'works'
    REJECT = 'reject'
    id = peewee.AutoField(primary_key=True)
    state = peewee.CharField(choices=[WORKS, REJECT])
    bag = peewee.ForeignKeyField(CredentialBag, backref='credentials')
    service = peewee.ForeignKeyField(Service, backref='credentials')
    sudo = peewee.BooleanField(default=False)

    def __str__(self):
        flags = ""

        if self.sudo:
            flags += SUDO_FLAG

        return "{}:{}{}".format(self.bag.username, self.bag.password, flags)

    def __repr__(self):
        return "<Credential {}>".format(self.__str__())


class Flag(BaseModel):
    id = peewee.AutoField(primary_key=True)
    team = peewee.ForeignKeyField(Team, backref='flags')
    name = peewee.CharField(max_length=150)


class CaptureNote(BaseModel):
    id = peewee.AutoField(primary_key=True)
    flag = peewee.ForeignKeyField(Flag, backref='notes')
    service = peewee.ForeignKeyField(Service, backref='flag_notes')
    data = peewee.TextField()
    location = peewee.CharField(max_length=200)
    notes = peewee.TextField(null=True)
    searched = peewee.BooleanField(default=False)

    def __str__(self):
        flags = ""

        if "Used Sudo" in self.notes:
            flags += SUDO_FLAG

        return "{} -> {}{}".format(self.location, self.data, flags)


def create():  # pragma: no cover
    database_proxy.create_tables([CredentialBag, Team, Service, Credential, Flag, CaptureNote])


def delete():  # pragma: no cover
    CredentialBag.delete().execute()
    Team.delete().execute()
    Service.delete().execute()
    Credential.delete().execute()
    Flag.delete().execute()
    CaptureNote.delete().execute()
