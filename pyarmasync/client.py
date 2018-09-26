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

"""Module for repository consumer operations."""

import os

from . import configuration, utils


class Client(object):
    """Provide operations on a repository client."""

    def __init__(self, path: str, repository_url: str) -> None: # pragma: no-cover
        """Initialize object."""
        self.path = path
        self.remote = Remote(repository_url)

    @staticmethod
    def check_presence(path: str) -> bool:
        """Check whether the directory at `path` is a Client."""
        abs_directory = os.path.abspath(path)
        index_directory = os.path.join(abs_directory, configuration.index_directory)
        index_file = os.path.join(index_directory, configuration.client_index)

        return all([
            os.path.isdir(abs_directory),
            os.path.isdir(index_directory),
            os.path.isfile(index_file),
        ])

    @classmethod
    def create(cls, path: str, url: str, overwrite: bool) -> 'Client':
        """Create new client at `path` linked with repository at `url`."""
        client_path = os.path.abspath(path)
        if not os.path.isdir(client_path):
            try:
                os.makedirs(client_path, exist_ok=True)
            except PermissionError:
                raise

        index_dir = os.path.join(client_path, configuration.index_directory)
        index_file = os.path.join(index_dir, configuration.client_index)

        if cls.check_presence(client_path) and not overwrite:
                index_content = utils.read_metadata(index_file)
                return cls(client_path, index_content['remote_url'])

        # Create index directory and file

        os.makedirs(index_dir, exist_ok=True)
        index_content = {'remote_url': url, 'configuration_version': configuration.version}
        utils.write_metadata(index_file, index_content)

        # Return newly created client
        return cls(client_path, url)


class Remote(object):
    """Middleware to access a repository."""

    def __init__(self, url: str) -> None:
        """Initialize object."""
        self._url = utils.RepositoryURL(url)

    @property
    def url(self) -> str:
        """Hide internal usage of `RepositoryURL`."""
        return self._url.url
