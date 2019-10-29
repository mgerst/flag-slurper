"""
Based heavily on pipenv's shell functionality: https://github.com/pypa/pipenv/blob/master/pipenv/shells.py
"""
import contextlib
import os
import subprocess

import sys

import click
import shellingham
from vistir import temp_environ

from flag_slurper import utils


def detect_info():
    try:
        return shellingham.detect_shell()
    except (shellingham.ShellDetectionFailure, TypeError):
        raise shellingham.ShellDetectionFailure


def _handover(cmd, args):
    args = [cmd] + args
    if os.name != 'nt':
        os.execvp(cmd, args)
    else:
        sys.exit(subprocess.call(args, shell=True, universal_newlines=True))


class Shell:
    def __init__(self, cmd):
        self.cmd = cmd
        self.args = []

    def __repr__(self):
        return '{type}(cmd={cmd!r})'.format(
            type=type(self).__name__,
            cmd=self.cmd,
        )

    @contextlib.contextmanager
    def inject_project(self, project):
        with temp_environ():
            name = os.path.basename(project)
            if 'PROMPT' in os.environ:
                os.environ['PROMPT'] = f"({name}) {os.environ['PROMPT']}"
            if 'PS1' in os.environ:
                os.environ['PS1'] = f"({name}) {os.environ['PS1']}"

            os.environ['SLURPER_PROJECT'] = project
            yield

    def fork(self, project, cwd, args):
        with self.inject_project(project):
            os.chdir(cwd)
            _handover(self.cmd, self.args + list(args))


def choose_shell():
    _type, command = detect_info()
    return Shell(command)


@click.command()
@click.argument('project', metavar='BASE', type=click.Path())
def shell(project):
    shell = choose_shell()
    utils.report_status('Launching shell in project')

    fork_args = (
        str(project),
        os.getcwd(),
        [],
    )

    shell.fork(*fork_args)
