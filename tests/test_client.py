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

import pyarmasync.client as unit

import pytest


@pytest.mark.parametrize('isdir_outcome,result', [(True, True), (False, False)])
def test_check_presence(mocker, isdir_outcome, result):
    """Assert True is returned when directory is a Client."""
    mocker.patch('os.path.isdir', return_value=isdir_outcome)
    mocker.patch('os.path.isfile')

    assert unit.Client.check_presence('foo') == result
