import click
import pytest

from flag_slurper.autolib.models import CredentialBag, Credential, CaptureNote

SUDO_FLAG = click.style('!', fg='red', bold=True)


def test_cred_bag__str__(bag):
    assert bag.__str__() == "root:cdc"


def test_cred_bag__repr__(bag):
    assert bag.__repr__() == "<CredentialBag: root:cdc>"


def test_cred__str__(credential):
    assert credential.__str__() == "root:cdc"


def test_cred__repr__(credential):
    assert credential.__repr__() == "<Credential: root:cdc>"


def test_cred_sudo__str__(sudocred):
    assert sudocred.__str__() == "cdc:cdc{}".format(SUDO_FLAG)


def test_cred_sudo__repr__(sudocred):
    assert sudocred.__repr__() == "<Credential: cdc:cdc{}>".format(SUDO_FLAG)


def test_capture_note__str__(flag, service):
    note = CaptureNote(flag=flag, service=service, data='abcd', location='/root/test.flag', notes='did stuff')
    assert note.__str__() == "/root/test.flag -> abcd"


def test_capture_note_sudo__str__(flag, service):
    note = CaptureNote(flag=flag, service=service, data='abcd', location='/root/test.flag', notes='did stuff\nUsed Sudo')
    assert note.__str__() == "/root/test.flag -> abcd{}".format(SUDO_FLAG)
