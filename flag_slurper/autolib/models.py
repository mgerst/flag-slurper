import peewee
import playhouse.db_url

# We want to allow setting up the database connection from .flagrc
database_proxy = peewee.Proxy()


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


def create():  # pragma: no cover
    database_proxy.create_tables([CredentialBag, Team, Service, Credential])
