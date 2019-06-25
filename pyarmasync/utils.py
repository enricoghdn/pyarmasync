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

"""
Collection of utility classes, methods and variables.

This package also contains functions used by different components to provide a common standard
concerning paths and serialization of application data.
"""

import os
from typing import Any
from urllib.parse import urlparse

import msgpack

from pyarmasync import configuration

from . import exceptions


class RepositoryURL(object):
    """Ensure URLs pointing to repositories are valid across the whole system."""

    supported_url_schemas = ('file', 'http', 'https')

    def __init__(self, url: str) -> None:
        """Initialize object."""
        if not self.valid_url(url):
            raise exceptions.InvalidURL('URL must be compliant to RFC2396')
        if not self.supported_url(url):
            raise exceptions.UnsupportedURLSchema('URL schema is not supported')
        self.url = url

    @staticmethod
    def valid_url(url: str) -> bool:
        """Check if string `url` is a valid URL compliant to RFC2396."""
        parsed_url = urlparse(url)

        return all([parsed_url.scheme, parsed_url.netloc])

    @classmethod
    def supported_url(cls, url: str) -> bool:
        """Check if string `url` is supported."""
        parsed_url = urlparse(url)

        return parsed_url.scheme in cls.supported_url_schemas


def write_metadata(to: str, data: Any) -> None:
    """Write application metadata on a file ensuring a consistent format is used."""
    try:
        os.makedirs(os.path.dirname(to), exist_ok=True)
    except PermissionError:
        raise
    with open(to, mode='w+b') as dest:
        dest.write(to_persistence_format(data))


def read_metadata(file: str) -> Any:
    """Read application metadata from a file."""
    if not os.path.isfile(file):
        raise ValueError('Not a file.')
    with open(file, mode='r+b') as source:
        content = source.read()

    return from_persistence_format(content)


def to_persistence_format(data: Any) -> Any:
    """Transform application data to the format used for persistence."""
    return msgpack.packb(data)


def from_persistence_format(data: Any) -> Any:
    """Transform persistence data to application data."""
    return msgpack.unpackb(data, use_list=False, raw=False)


def repository_index_file_path(repository_path: str) -> str:
    """Construct the path for a repository index file."""
    return os.path.join(repository_path, configuration.index_directory, configuration.index_file)


def repository_tree_file_path(repository_path: str) -> str:
    """Construct the path for a repository tree file."""
    return os.path.join(repository_path, configuration.index_directory, configuration.tree_file)


def build_url(baseurl: str, *args: str) -> str:
    """Append segments to path of given url."""
    res = baseurl
    for segpath in args:
        res = res if res.endswith('/') else res + '/'
        res = res + segpath

    return res
