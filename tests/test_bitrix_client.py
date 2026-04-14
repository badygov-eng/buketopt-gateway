"""Unit-тесты разбора ответов Bitrix."""

import pytest

from gateway.bitrix_client import BitrixRestError, _parse_json_safe


def test_parse_json_invalid() -> None:
    with pytest.raises(BitrixRestError):
        _parse_json_safe("not json")


def test_parse_json_array() -> None:
    with pytest.raises(BitrixRestError):
        _parse_json_safe("[1]")
