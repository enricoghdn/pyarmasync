# --------------------------------License Notice----------------------------------
# pyarmasync - Arma3 mod synchronization tool
#
# Copyright (C) 2018 Enrico Ghidoni (enricoghdn@gmail.com)
# Copyright (C) 2018 Carpe Noctem - Tactical Operations (aka. CNTO) (contact@carpenoctem.co)
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

"""Provide an interface for operations on a repository."""

import os
import zlib
from typing import Dict, Iterable, List

from . import configuration, utils


def list_files(path: str, bl_subdirs: Iterable[str] = None, bl_extensions: Iterable[str] = None) \
        -> List:
    """List the absolute path to every file in a directory, subdirectories included."""
    if bl_subdirs is None:
        bl_subdirs = tuple()
    if bl_extensions is None:
        bl_extensions = tuple()

    dir_list = os.walk(path)
    file_list = []

    for dir_entry in dir_list:
        skip = False
        for bl_subdir in bl_subdirs:
            if bl_subdir in dir_entry[0].replace(path, ''):
                skip = True
        if skip:
            continue
        for file in dir_entry[2]:
            add = True
            for bl_extension in bl_extensions:
                if file.endswith(bl_extension):
                    add = False
            if add:
                file_list.append(dir_entry[0] + '/' + file)

    return file_list


def file_checksum(path: str) -> int:
    """Compute adler32 checksum of the whole content of a file."""
    with open(path, mode='rb') as file:
        checksum = zlib.adler32(file.read())

    return checksum


class Repository(object):
    """Wrap operations on a directory that contains a repository."""

    def __init__(self, path: str, url: str, display_name: str = None) -> None:
        """Initialize object properties."""
        self.repo_path: str = os.path.abspath(path)
        self.url = utils.RepositoryURL(url)
        self.display_name = display_name
        self.config_version = configuration.version

        self._index_subdir: str = configuration.index_directory
        self._index_path: str = os.path.join(self.repo_path, self._index_subdir)
        self._index_file_path: str = os.path.join(self._index_path, configuration.index_file)
        self._tree_file_path: str = os.path.join(self._index_path, configuration.tree_file)
        self._sync_file_extension: str = configuration.extension

        # Contains whole file checksums to quickly check if a file has been updated
        self.file_checksums: Dict[str, int] = {}

    @staticmethod
    def check_presence(directory: str) -> bool:
        """Check if `directory` contains an initialized repository."""
        abs_directory = os.path.abspath(directory)
        index_subdirectory = os.path.join(abs_directory, configuration.index_directory)
        index_file_path = os.path.join(index_subdirectory, configuration.index_file)

        return all([
            os.path.isdir(abs_directory),
            os.path.isdir(index_subdirectory),
            os.path.isfile(index_file_path),
        ])

    @classmethod
    def initialize(cls, directory: str, display_name: str, url: str, overwrite: bool = False) \
            -> 'Repository':
        """Create new repository using `directory` as location."""
        path = os.path.abspath(directory)
        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
            except PermissionError:
                raise

        if cls.check_presence(directory) and not overwrite:
            return cls(directory, url)

        index_directory_path = os.path.join(directory, configuration.index_directory)
        os.makedirs(index_directory_path, exist_ok=True)

        index_file_path = os.path.join(index_directory_path, configuration.index_file)
        repository_index = {'display_name': display_name, 'url': url,
                            'configuration_version': configuration.version,
                            'index_file_name': configuration.index_file,
                            'sync_file_extension': configuration.extension}

        utils.write_metadata(index_file_path, repository_index)

        return cls(directory, url)

    def build(self) -> None:
        """Update repository to reflect file changes."""
        self._clean_tree()

        updated_files: Dict[str, int] = self._detect_updated_files()
        for file, checksum in updated_files.items():
            self.file_checksums[file] = checksum
            self._update_synchronization_file(file)

        self._update_index_file()
        self._update_tree_file()
        self._clean_repository()

    def _detect_updated_files(self) -> Dict[str, int]:
        """Return updated files path and whole file checksum."""
        file_list = list_files(self.repo_path, [self._index_subdir],
                               [self._sync_file_extension])
        updated_files: Dict[str, int] = {}

        for file in file_list:
            whole_file_checksum: int = file_checksum(file)
            if file not in self.file_checksums or whole_file_checksum != self.file_checksums[file]:
                updated_files[file] = whole_file_checksum

        return updated_files

    def _clean_tree(self) -> None:
        """Remove nonexistent files from object tree."""
        self.file_checksums = {key: val for key, val in self.file_checksums.items()
                               if os.path.isfile(key)}

    def _update_index_file(self) -> None:
        """Update repository index file to reflect object status."""
        content = {'display_name': self.display_name, 'url': self.url.url,
                   'configuration_version': self.config_version,
                   'index_file_path': self._relative_to_repo(self._index_file_path),
                   'tree_file_path': self._relative_to_repo(self._tree_file_path),
                   'sync_file_extension': self._sync_file_extension,
                   }

        utils.write_metadata(self._index_file_path, content)

    def _update_tree_file(self) -> None:
        """Update repository tree file according to object's tree."""
        utils.write_metadata(self._tree_file_path, self.file_checksums)

    def _update_synchronization_file(self, file: str) -> None:
        """Generate and store synchronization data for `file`."""
        sync_data: int = self.file_checksums[file]
        sync_file_path: str = file + self._sync_file_extension

        utils.write_metadata(sync_file_path, sync_data)

    def _clean_repository(self) -> None:
        """Remove orphaned synchronization files."""
        all_files = list_files(self.repo_path, [self._index_subdir])

        for file in all_files:
            if file.endswith(self._sync_file_extension):
                tracked_file = file.replace(self._sync_file_extension, '')
                if not os.path.isfile(tracked_file):
                    os.remove(file)

    def _relative_to_repo(self, path: str) -> str:
        """Make `path` relative to the repository location."""
        return os.path.relpath(path, start=self.repo_path)
