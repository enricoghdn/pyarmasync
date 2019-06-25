# --------------------------------License Notice----------------------------------
# pyarmasync - Arma3 mod synchronization tool
#
# Copyright (C) 2018 Enrico Ghidoni (enricoghdn@gmail.com)
#
# The authors of this software are listed in the AUTHORS file at the
# root of this software's source code tree.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# All rights reserved.
# --------------------------------License Notice----------------------------------

"""Test suite for `pyarmasync.client`."""

import os
from builtins import ConnectionError

import pyarmasync.client as unit
import pyarmasync.configuration as configuration
import pyarmasync.utils as utils

import pytest

from .common import arg_in_call_list


class ClientCreationMock(object):
    """Wrap mocks for testing client creation method."""

    def __init__(self, mocker):  # noqa: D401
        """Setup mocks."""
        self.isdir = mocker.patch('os.path.isdir')
        self.makedirs = mocker.patch('os.makedirs')
        self.write_metadata = mocker.patch('pyarmasync.utils.write_metadata')
        self.read_metadata = mocker.patch('pyarmasync.utils.read_metadata')
        self.check_presence = mocker.patch('pyarmasync.client.Client.check_presence')


@pytest.fixture()
def creation_mock(mocker) -> ClientCreationMock:
    """Fixture generator."""
    return ClientCreationMock(mocker)


@pytest.mark.parametrize('isdir_outcome,result', [(True, True), (False, False)])
def test_check_presence(mocker, isdir_outcome, result):
    """Assert True is returned when directory is a Client."""
    mocker.patch('os.path.isdir', return_value=isdir_outcome)
    mocker.patch('os.path.isfile')

    assert unit.Client.check_presence('foo') == result


def test_create_ok(creation_mock):
    """Assert creation ok."""
    path = '/foo/bar'
    url = 'http://foo'
    overwrite = False

    creation_mock.isdir.return_value = True
    creation_mock.check_presence.return_value = False

    client = unit.Client.create(path, url, overwrite)

    index_directory = os.path.join(path, configuration.index_directory)
    index_file = os.path.join(index_directory, configuration.client_index)

    assert arg_in_call_list(index_directory, creation_mock.makedirs)
    assert arg_in_call_list(index_file, creation_mock.write_metadata)
    assert isinstance(client, unit.Client)


def test_create_no_dir(creation_mock):
    """Assert client path is created if it doesn't exist."""
    path = '/foo/bar'
    url = 'http://foo'
    overwrite = False

    creation_mock.isdir.return_value = False
    creation_mock.check_presence.return_value = False

    unit.Client.create(path, url, overwrite)

    assert arg_in_call_list(path, creation_mock.makedirs)


def test_create_permission_error(creation_mock):
    """Assert PermissionError is raised if no permissions to create the directory."""
    path = '/foo/bar'
    url = 'http://foo'
    overwrite = False

    creation_mock.isdir.return_value = False
    creation_mock.check_presence.return_value = False
    creation_mock.makedirs.side_effect = PermissionError()

    with pytest.raises(PermissionError):
        unit.Client.create(path, url, overwrite)


def test_create_existing_no_overwrite(creation_mock):
    """Assert values are read from existing client if `overwrite` is set to False."""
    path = '/foo/bar'
    url = 'http://foo'
    overwrite = False

    creation_mock.isdir.return_value = True
    creation_mock.check_presence.return_value = True
    creation_mock.read_metadata.return_value = {'remote_url': 'http://test'}

    client = unit.Client.create(path, url, overwrite)

    creation_mock.read_metadata.assert_called()
    assert client.proxy.url == 'http://test'


@pytest.mark.parametrize('url,expType', [
    ('http://weburl', unit.WebProxy),
    ('https://secureweburl', unit.WebProxy),
    ('file://localurl', unit.LocalProxy),
])
def test_proxy_creation_ok(url, expType):
    """Assert Proxy object creation works with the supported options."""
    proxy = unit.Proxy.factory(url)

    assert isinstance(proxy, expType)


def test_proxy_creation_unsupported():
    """Assert error is raised for unsupported url in proxy creation."""
    url = 'ftp://ftpurl'

    with pytest.raises(ValueError):
        unit.Proxy.factory(url)


def test_web_proxy_repository_index(mocker):
    """Assert repository index dictionary is fetched from URL and returned."""
    fixture = {'foo': 'bar', 'baz': 3}
    persistence_fixture = utils.to_persistence_format(fixture)

    url = 'http://weburl/' + configuration.index_directory + '/' + configuration.index_file

    make_request_mock = mocker.patch('pyarmasync.client.WebProxy._make_request')
    make_request_mock.return_value = persistence_fixture

    proxy = unit.Proxy.factory('http://weburl')

    assert proxy.repository_index() == fixture
    make_request_mock.assert_called_with(url)


def test_web_proxy_repository_tree(mocker):
    """Assert repository tree dictionary is fetched from URL and returned."""
    fixture = {'foo': 1, 'bar': 2}
    persistence_fixture = utils.to_persistence_format(fixture)

    url = 'http://weburl/' + configuration.index_directory + '/' + configuration.tree_file

    make_request_mock = mocker.patch('pyarmasync.client.WebProxy._make_request')
    make_request_mock.return_value = persistence_fixture

    proxy = unit.Proxy.factory('http://weburl')

    assert proxy.repository_tree() == fixture
    make_request_mock.assert_called_with(url)


def test_web_proxy_sync_file(mocker):
    """Assert repository sync file is fetched from URL and returned."""
    fixture = 123456789
    persistence_fixture = utils.to_persistence_format(fixture)

    filename = 'test'
    url = 'http://weburl/' + filename

    make_request_mock = mocker.patch('pyarmasync.client.WebProxy._make_request')
    make_request_mock.return_value = persistence_fixture

    proxy = unit.Proxy.factory('http://weburl')

    assert proxy.sync_file(file=filename) == fixture
    make_request_mock.assert_called_with(url + configuration.extension)


def test_web_proxy_make_request_ok(mocker):
    """Assert http request is sent and response content is returned."""
    urlopen_mock = mocker.patch('urllib.request.urlopen')
    urlopen_mock.return_value.read.return_value = 'test'
    urlopen_mock.return_value.code = 200

    proxy = unit.Proxy.factory('http://weburl')

    content = proxy._make_request('http://weburl')

    urlopen_mock.assert_called_once()
    assert content == 'test'


def test_web_proxy_make_request_not_ok(mocker):
    """Assert method raises error if response status code not ok."""
    urlopen_mock = mocker.patch('urllib.request.urlopen')
    urlopen_mock.return_value.code = 400
    urlopen_mock.return_value.reason = 'test'

    proxy = unit.Proxy.factory('http://weburl')

    with pytest.raises(ConnectionError):
        proxy._make_request('http://weburl')
