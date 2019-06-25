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
import urllib
import urllib.request
from abc import ABCMeta, abstractmethod
from pathlib import PurePath
from typing import Dict

from . import configuration, utils


class Client(object):
    """Provide operations on a repository client."""

    def __init__(self, path: str, repository_url: str) -> None:  # pragma: no-cover
        """Initialize object."""
        self.path = path
        self.proxy = Proxy.factory(repository_url)

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

        if not overwrite and cls.check_presence(client_path):
            # Found existing client, not overwriting, read existing configuration
            index_content = utils.read_metadata(index_file)
            return cls(client_path, index_content['remote_url'])

        # Create index directory and file

        os.makedirs(index_dir, exist_ok=True)
        index_content = {'remote_url': url, 'configuration_version': configuration.version}
        utils.write_metadata(index_file, index_content)

        # Return newly created client
        return cls(client_path, url)


class Proxy(metaclass=ABCMeta):
    """Base class for proxy components."""

    @staticmethod
    def factory(url: str) -> 'Proxy':  # noqa: D401
        """Factory method to get the proper proxy based on the url scheme."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme == 'http' or parsed.scheme == 'https':
            return WebProxy(url)
        elif parsed.scheme == 'file':
            return LocalProxy(url)
        else:
            raise ValueError('Unsupported scheme.')

    def __init__(self, url: str) -> None:  # pragma: no cover
        """Initialize object."""
        self._url = utils.RepositoryURL(url)

    @abstractmethod
    def repository_index(self) -> Dict:  # pragma: no cover
        """Get repository index dictionary."""
        pass

    @abstractmethod
    def repository_tree(self) -> Dict[str, int]:  # pragma: no cover
        """Get repository tree."""
        pass

    @abstractmethod
    def sync_file(self, file: str) -> bytes:  # pragma: no cover
        """Get sync file for `file`."""
        pass

    @property
    def url(self) -> str:
        """Hide internal usage of `RepositoryURL`."""
        return self._url.url


class WebProxy(Proxy):  # noqa: D412
    r"""Proxy implementation for http/https protocols.

    This proxy will make http/https requests to the indicated repository url, thus a web server
    must be correctly configured to properly serve such requests.
    The proxy will append to the provided ``url`` the relative path of the files it needs.
    There are three kind of files the proxy will make requests for:

        - index file: its relative path is ``configuration.index_directory``/ \
        ``configuration.index_file``

        - tree file : its relative path is ``configuration.index_directory``/ \
        ``configuration.tree_file``

        - sync files: as many as the files to keep synchronized, sync files are located in the \
        repository's main directory

    Example:
        Taking as example a repository with url = 'http://foo.com/bar/repo' containing a single
        file named ``lorem`` in its main directory, this proxy will make the following http
        requests:

        - index file: 'http://foo.com/bar/repo/.pyarmasync/repoinfo'
        - tree file : 'http://foo.com/bar/repo/.pyarmasync/repotree'
        - sync file : 'http://foo.com/bar/repo/lorem.pyarmasync'

    Notes:

        - The relative path is based on the above mentioned configuration parameters.
        - The proxy will make a sync file request for every file in the repository. This accounts \
        for a total of N+2 requests where N is the amount of files contained by the repository.

    """

    def __init__(self, url: str) -> None:  # pragma: no cover
        """Initialize object."""
        super().__init__(url)

    def repository_index(self) -> Dict:  # noqa: D102
        # Build http url for index file
        index_url = utils.build_url(
            self.url,
            configuration.index_directory,
            configuration.index_file,
        )

        return utils.from_persistence_format(self._make_request(index_url))

    def repository_tree(self) -> Dict[str, int]:  # noqa: D102
        tree_url = utils.build_url(
            self.url,
            configuration.index_directory,
            configuration.tree_file,
        )

        return utils.from_persistence_format(self._make_request(tree_url))

    def sync_file(self, file: str) -> bytes:  # noqa: D102
        file_url = utils.build_url(
            self.url,
            file + configuration.extension,
        )

        return utils.from_persistence_format(self._make_request(file_url))

    def _make_request(self, url: str) -> bytes:
        """Make a request to given url and return response content."""
        response = urllib.request.urlopen(url)
        # Disabling type check on usage of response object since no formal definition
        # exists (see https://docs.python.org/3/library/urllib.request.html)
        if response.code not in range(200, 299):  # type: ignore
            raise ConnectionError(response.reason)  # type: ignore

        return response.read()


class LocalProxy(Proxy):
    """Proxy implementation for local files."""

    def __init__(self, url: str) -> None:
        """Initialize object."""
        super().__init__(url)

    def repository_index(self) -> Dict:  # noqa: D102
        return self._do_read_file(self.url, configuration.index_directory,
                                  configuration.index_file)

    def repository_tree(self) -> Dict[str, int]:  # noqa: D102
        return self._do_read_file(self.url, configuration.index_directory, configuration.tree_file)

    def sync_file(self, file: str) -> bytes:  # noqa: D102
        # return self._do_read_file(self.url, file)
        pass

    def _do_read_file(self, url: str, *args: str) -> Dict:
        """Read repository info from file given the repo url and file path."""
        abspath = self._build_file_absolute_path_from_url(url, *args)
        return utils.read_metadata(str(abspath))

    def _build_file_absolute_path_from_url(self, url: str, *args: str) -> PurePath:
        """Build an absolute path from given segments taking url as base."""
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            # Absolute path is given
            abspath = PurePath(parsed.path)
        else:
            # Relative path is given
            absolutized = os.path.abspath(parsed.netloc + parsed.path)
            abspath = PurePath(absolutized)

        for segment in args:
            abspath = PurePath(abspath, segment)

        return abspath
