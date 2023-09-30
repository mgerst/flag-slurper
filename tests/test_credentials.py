from click.testing import CliRunner

from flag_slurper.cli import cli
from flag_slurper.autolib.models import CredentialBag, Credential
from flag_slurper.conf.project import Project
from tests.conftest import cli_runner


def test_add_credentials(db, cli_runner):
    result = cli_runner(['creds', 'add', 'root', 'cdc'])
    assert result.exit_code == 0
    assert result.output == "[+] Added root:cdc\n"

    count = CredentialBag.select().where(CredentialBag.username == 'root', CredentialBag.password == 'cdc').count()
    assert count == 1


def test_ls_credentials(db, cli_runner):
    CredentialBag.create(username='root', password='cdc')
    result = cli_runner(['creds', 'ls'])
    assert result.exit_code == 0
    assert result.output == "Username:Password\nroot:cdc\n"


def test_rm_credential(db, cli_runner):
    CredentialBag.create(username='root', password='cdc')
    result = cli_runner(['creds', 'rm', 'root', 'cdc'])
    assert result.exit_code == 0
    count = CredentialBag.select().where(CredentialBag.username == 'root', CredentialBag.password == 'cdc').count()
    assert count == 0


def test_rm_credentials(db, cli_runner):
    CredentialBag.create(username='root', password='cdc')
    CredentialBag.create(username='root', password='root')
    result = cli_runner(['creds', 'rm', 'root'])
    assert result.exit_code == 0
    count = CredentialBag.select().where(CredentialBag.username == 'root').count()
    assert count == 0


def test_show_empty_creds(db, cli_runner):
    result = cli_runner(['creds', 'show', 'root'])
    assert result.exit_code == 3
    assert result.output == "No credentials matching this query\n"


def test_show_username(service, cli_runner):
    bag = CredentialBag.create(username='root', password='cdc')
    Credential.create(bag=bag, service=service, state='works')
    result = cli_runner(['creds', 'show', 'root:cdc'])
    assert result.exit_code == 0
    assert result.output == "Credential: root:cdc\n" \
                            "------------ [ Found Credentials ] ------------\n" \
                            "1/www.team1.isucdc.com:80: works\n\n\n\n"


def test_show_empty_bag(db, cli_runner):
    CredentialBag.create(username='root', password='cdc')
    result = cli_runner(['creds', 'show', 'root:cdc'])
    assert result.exit_code == 0
    assert result.output == "Credential: root:cdc\n" \
                            "------------ [ Found Credentials ] ------------\n" \
                            "This credential bag has no hits\n\n\n\n"


def test_creds_no_project():
    p = Project.get_instance()
    p.project_data = None
    runner = CliRunner()
    result = runner.invoke(cli, ['-np', 'creds', 'ls'])
    assert result.exit_code == 4
    assert result.output == "[!] Credentials commands require an active project\n"
