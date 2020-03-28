from abc import ABC, abstractmethod
from typing import Iterable, Type

import click
from terminaltables import AsciiTable

from .. import utils
from ..autolib.models import ShadowEntry


class BaseFormatter(ABC):
    """
    The base class for all shadow output formatters.
    """

    pageable = False

    @staticmethod
    @abstractmethod
    def format(shadows: Iterable[ShadowEntry]) -> str:  # pragma: no cover
        pass


class TableFormatter(BaseFormatter):
    pageable = True

    @staticmethod
    def format(shadows: Iterable[ShadowEntry]) -> str:
        data = [[s.id, s.service.team.number, s.service.service_name, s.source.path, s.username,
                 s.hash] for s in shadows]
        data.insert(0, ['ID', 'Team', 'Service', 'File', 'Username', 'Hash'])
        table = AsciiTable(data)
        return table.table


class TextFormatter(BaseFormatter):
    @staticmethod
    def format(shadows: Iterable[ShadowEntry]) -> str:
        data = [s.hash for s in shadows]
        return '\n'.join(data)


FORMATTER_MAP = {
    'table': TableFormatter,
    'hashcat': TextFormatter,
    'text': TextFormatter,
}


def display_format(shadows: Iterable[ShadowEntry], format: str):
    if format not in FORMATTER_MAP:
        utils.report_error(f'Requested format `{format}` does not exist')
        return

    formatter = FORMATTER_MAP[format]
    output = formatter.format(shadows)

    if formatter.pageable:
        utils.conditional_page(output, len(shadows) + 1)
    else:
        click.echo(output)
