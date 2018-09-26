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

"""Test suite for `pyarmasync.utils`."""

import msgpack

import pyarmasync.exceptions as exceptions
import pyarmasync.utils as unit

import pytest


@pytest.mark.parametrize('url', [
    'http://',
    'ftp:/malformed',
    '://onlyhost',
])
def test_repository_url_invalid_url(url):
    """Assert exception is raised if url is invalid."""
    with pytest.raises(exceptions.InvalidURL):
        unit.RepositoryURL(url)


def test_init_repo_unsupported_schema():
    """Assert exception is raised if unsupported url schema is passed."""
    with pytest.raises(exceptions.UnsupportedURLSchema):
        unit.RepositoryURL('sftp://something')


def test_init_ok():
    """Assert object creation works fine."""
    unit.RepositoryURL('http://foo')


def test_write_metadata(mocker):
    """Assert data is passed correctly to system write."""
    mock_open = mocker.patch('builtins.open')

    payload = {'foo': 'bar', 'baz': 5}
    filename = '/file'
    expected_content = msgpack.packb(payload)

    unit.write_metadata(to=filename, data=payload)

    mock_open.return_value.__enter__.return_value.write.assert_called_with(expected_content)


def test_write_permission_error(mocker):
    """Assert PermissionError is raised."""
    mocker.patch('os.makedirs', side_effect=PermissionError)

    with pytest.raises(PermissionError):
        unit.write_metadata('foo', None)


def test_read_metadata(mocker):
    """Assert data is read correctly."""
    mock_open = mocker.patch('builtins.open')
    mocker.patch('os.path.isfile', return_value=True)

    expected_content = {'foo': 'bar', 'baz': 5}
    content = msgpack.packb(expected_content)
    filename = '/file'

    mock_open.return_value.__enter__.return_value.read.return_value = content

    result = unit.read_metadata(filename)

    assert result == expected_content


def test_read_metadata_not_a_file(mocker):
    """Assert ValueError is passed if path is not a file."""
    mocker.patch('os.path.isfile', return_value=False)

    with pytest.raises(ValueError):
        unit.read_metadata('file')
