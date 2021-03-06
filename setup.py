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

"""Setuptools-backed setup module."""

import codecs
import os

import setuptools


if __name__ == '__main__':
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

    # Use README.md as source for setuptools.setup's long_description param
    with codecs.open(os.path.join(ROOT_DIR, 'README.md'),
                     encoding='utf-8') as f:
        LONG_DESCRIPTION = f.read()

    setuptools.setup(
        # Distutils parameters
        name='pyarmasync',
        description='Open Source ArmA3 mod synchronization tool',
        long_description=LONG_DESCRIPTION,
        author='Enrico Ghidoni',
        url='https://github.com/enricoghdn/pyarmasync',
        packages=setuptools.find_packages(exclude=['tests']),
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Environment :: Console',
            'Environment :: X11 Applications :: Qt',
            'Environment :: Win32 (MS Windows)',
            'Programming Language :: Python :: 3',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Natural Language :: English',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3.6',
            'Topic :: Internet :: WWW/HTTP',
            'Topic :: Software Development :: Build Tools',
            'Topic :: System :: Software Distribution',
            'Topic :: Utilities',
        ],
        license='GNU General Public License Version 3',
        keywords='arma3 mods sync synchronisation http',
        # Setuptools parameters
        include_package_data=True,
        install_requires=[
            'msgpack>=0.5.6,<1',
        ],
        extras_require={
            'dev': [
                'ipython>=6.1,<7',
            ],
            'test': [
                'tox>=3.2.1,<4',
                'pytest>=3.4.2,<4',
                'pytest-mock>=1.5,<2',
            ],
            'docs': [
                'sphinx>=1.7.2,<2',
            ],
        },
        python_requires='>=3.6,<4',
        setup_requires=['setuptools_scm'],
        # setuptools_scm parameters
        use_scm_version=True,
    )
