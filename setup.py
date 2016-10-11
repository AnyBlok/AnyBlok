# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import os
import sys
from setuptools import setup, find_packages
version = '0.9.2'


if sys.version_info < (3, 3):
    sys.stderr.write("This package requires Python 3.3 or newer. "
                     "Yours is " + sys.version + os.linesep)
    sys.exit(1)

requires = [
    'sqlalchemy',
    'sqlalchemy-utils',
    'argparse',
    'alembic',
    'graphviz',
    'nose',  # for unittest during the blok install
    'lxml',
    'six',
    'PyYAML',
    'appdirs',
    'sqlalchemy-utils',
    'pytz',
    'python-dateutil',
    'texttable',
    'testfixtures',
]

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), 'r', encoding='utf-8') as readme:
    README = readme.read()

with open(
    os.path.join(here, 'doc', 'CHANGES.rst'), 'r', encoding='utf-8'
) as change:
    CHANGE = change.read()

with open(
    os.path.join(here, 'doc', 'FRONT.rst'), 'r', encoding='utf-8'
) as front:
    FRONT = front.read()

setup(
    name="AnyBlok",
    version=version,
    author="Jean-Sébastien Suzanne",
    author_email="jssuzanne@anybox.fr",
    description="Anyblok is a dynamic injection blok framework",
    license="MPL2",
    long_description=README + '\n' + FRONT + '\n' + CHANGE,
    url="http://docs.anyblok.org/%s" % version,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=requires,
    tests_require=requires + ['nose'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
    ],
    entry_points={
        'console_scripts': [
            'anyblok_createdb=anyblok.scripts:anyblok_createdb',
            'anyblok_updatedb=anyblok.scripts:anyblok_updatedb',
            'anyblok_nose=anyblok.scripts:anyblok_nose',
            'anyblok_interpreter=anyblok.scripts:anyblok_interpreter',
            'anyblok_cron_worker=anyblok.scripts:anyblok_cron_worker',
            'anyblok_doc=anyblok.scripts:anyblok2doc',
        ],
        'bloks': [
            'anyblok-core=anyblok.bloks.anyblok_core:AnyBlokCore',
            'model_authz='
            'anyblok.bloks.model_authz:ModelBasedAuthorizationBlok',
            'anyblok-io=anyblok.bloks.io:AnyBlokIO',
            'anyblok-io-csv=anyblok.bloks.io_csv:AnyBlokIOCSV',
            'anyblok-io-xml=anyblok.bloks.io_xml:AnyBlokIOXML',
        ],
        'test_bloks': [
            'test-blok1=anyblok.test_bloks.test_blok1:TestBlok',
            'test-blok2=anyblok.test_bloks.test_blok2:TestBlok',
            'test-blok3=anyblok.test_bloks.test_blok3:TestBlok',
            'test-blok4=anyblok.test_bloks.test_blok4:TestBlok',
            'test-blok5=anyblok.test_bloks.test_blok5:TestBlok',
            'test-blok6=anyblok.test_bloks.test_blok6:TestBlok',
            'test-blok7=anyblok.test_bloks.test_blok7:TestBlok',
            'test-blok8=anyblok.test_bloks.test_blok8:TestBlok',
            'test-blok9=anyblok.test_bloks.test_blok9:TestBlok',
            'test-blok10=anyblok.test_bloks.test_blok10:TestBlok',
            'test-blok11=anyblok.test_bloks.test_blok11:TestBlok',
            'test-blok12=anyblok.test_bloks.test_blok12:TestBlok',
            'test-blok13=anyblok.test_bloks.test_blok13:TestBlok',
        ],
        'nose.plugins.0.10': [
            'anyblok-bloks=anyblok.plugins:AnyBlokPlugin',
        ],
        'anyblok.init': [],
    },
    extras_require={},
)
