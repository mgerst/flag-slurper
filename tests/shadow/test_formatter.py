from flag_slurper.shadow.formatters import TableFormatter, TextFormatter, display_format


def test_table_formatter(shadow):
    formatted = TableFormatter.format([shadow])
    assert '+----' in formatted
    assert shadow.service.service_name in formatted


def test_text_formatter(shadow):
    formatted = TextFormatter.format([shadow])
    assert formatted == shadow.hash


def test_display_format_does_not_exist(shadow):
    formatted = display_format([shadow], 'foobar')
    assert formatted is None


def test_display_format_pageable(shadow, mocker):
    conditional_page = mocker.patch('flag_slurper.shadow.formatters.utils.conditional_page')
    display_format([shadow], 'table')
    assert conditional_page.called


def test_display_format_standard(shadow, mocker):
    echo = mocker.patch('flag_slurper.shadow.formatters.click.echo')
    display_format([shadow], 'text')
    assert echo.called
