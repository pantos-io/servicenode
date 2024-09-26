import unittest.mock

import pytest
import semantic_version  # type: ignore

from pantos.servicenode.protocol import get_latest_protocol_version
from pantos.servicenode.protocol import get_supported_protocol_versions
from pantos.servicenode.protocol import is_supported_protocol_version


def _to_semantic_version(version):
    return semantic_version.Version(version)


def _to_semantic_versions(*versions):
    return {_to_semantic_version(version) for version in versions}


_SUPPORTED_PROTOCOL_VERSIONS_SMALL = _to_semantic_versions('1.0.0')

_LATEST_PROTOCOL_VERSION_SMALL = _to_semantic_version('1.0.0')

_SUPPORTED_PROTOCOL_VERSIONS_MEDIUM = _to_semantic_versions(
    '1.0.0', '0.1.0', '0.1.1')

_LATEST_PROTOCOL_VERSION_MEDIUM = _to_semantic_version('1.0.0')

_SUPPORTED_PROTOCOL_VERSIONS_LARGE = _to_semantic_versions(
    '1.0.0', '0.9.5', '2.0.10', '0.1.0', '2.0.9', '2.0.0', '0.1.1')

_LATEST_PROTOCOL_VERSION_LARGE = _to_semantic_version('2.0.10')


@pytest.mark.parametrize(
    'supported_protocol_versions, latest_protocol_version',
    [(_SUPPORTED_PROTOCOL_VERSIONS_SMALL, _LATEST_PROTOCOL_VERSION_SMALL),
     (_SUPPORTED_PROTOCOL_VERSIONS_MEDIUM, _LATEST_PROTOCOL_VERSION_MEDIUM),
     (_SUPPORTED_PROTOCOL_VERSIONS_LARGE, _LATEST_PROTOCOL_VERSION_LARGE)])
def test_get_latest_protocol_version_correct(supported_protocol_versions,
                                             latest_protocol_version):
    with unittest.mock.patch(
            'pantos.servicenode.protocol._SUPPORTED_PROTOCOL_VERSIONS',
            supported_protocol_versions):
        assert get_latest_protocol_version() == latest_protocol_version


@pytest.mark.parametrize('supported_protocol_versions', [
    _SUPPORTED_PROTOCOL_VERSIONS_SMALL, _SUPPORTED_PROTOCOL_VERSIONS_MEDIUM,
    _SUPPORTED_PROTOCOL_VERSIONS_LARGE
])
def test_get_supported_protocol_versions_correct(supported_protocol_versions):
    with unittest.mock.patch(
            'pantos.servicenode.protocol._SUPPORTED_PROTOCOL_VERSIONS',
            supported_protocol_versions):
        assert get_supported_protocol_versions() == sorted(
            supported_protocol_versions)


@pytest.mark.parametrize(
    'supported_protocol_versions, protocol_version, is_supported',
    [(_SUPPORTED_PROTOCOL_VERSIONS_SMALL, '1.0.0', True),
     (_SUPPORTED_PROTOCOL_VERSIONS_SMALL, '1.1.0', False),
     (_SUPPORTED_PROTOCOL_VERSIONS_MEDIUM, '0.1.0', True),
     (_SUPPORTED_PROTOCOL_VERSIONS_MEDIUM, '2.0.0', False),
     (_SUPPORTED_PROTOCOL_VERSIONS_LARGE, '2.0.0', True),
     (_SUPPORTED_PROTOCOL_VERSIONS_LARGE, '3.0.1', False)])
def test_is_supported_protocol_version_correct(supported_protocol_versions,
                                               protocol_version, is_supported):
    with unittest.mock.patch(
            'pantos.servicenode.protocol._SUPPORTED_PROTOCOL_VERSIONS',
            supported_protocol_versions):
        assert is_supported_protocol_version(
            _to_semantic_version(protocol_version)) is is_supported
