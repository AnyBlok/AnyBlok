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
version = '0.2.0'


if sys.version_info < (3, 2):
    sys.stderr.write("This package requires Python 3.2 or newer. "
                     "Yours is " + sys.version + os.linesep)
    sys.exit(1)

requires = [
    'sqlalchemy',
    'argparse',
    'alembic',
    'graphviz',
]

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as readme:
    README = readme.read()

setup(
    name="AnyBlok",
    version=version,
    author="Jean-Sébastien Suzanne",
    author_email="jssuzanne@anybox.fr",
    description="Anyblok is a dynamic injection blok framework",
    license="MPL2",
    long_description=README,
    url="http://docs.anyblok.org/%s" % version,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=requires,
    tests_require=requires + ['nose'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
    ],
    entry_points={
        'AnyBlok': [
            'anyblok-core=anyblok.bloks.anyblok_core:AnyBlokCore',
            'anyblok-io=anyblok.bloks.io:AnyBlokIO',
            'anyblok-io-csv=anyblok.bloks.io_csv:AnyBlokIOCSV',
        ],
        'TestAnyBlok': [
            'test-blok1=anyblok.test_bloks.test_blok1:TestBlok',
            'test-blok2=anyblok.test_bloks.test_blok2:TestBlok',
            'test-blok3=anyblok.test_bloks.test_blok3:TestBlok',
            'test-blok4=anyblok.test_bloks.test_blok4:TestBlok',
            'test-blok5=anyblok.test_bloks.test_blok5:TestBlok',
            'test-blok6=anyblok.test_bloks.test_blok6:TestBlok',
            'test-blok7=anyblok.test_bloks.test_blok7:TestBlok',
            'test-blok8=anyblok.test_bloks.test_blok8:TestBlok',
        ],
    },
    extras_require={},
)
