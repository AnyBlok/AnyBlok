import os
import sys
from setuptools import setup, find_packages
version = '0.0.1'


if sys.version_info < (3, 3):
    sys.stderr.write("This package requires Python 3.3 or newer. "
                     "Yours is " + sys.version + os.linesep)
    sys.exit(1)

requires = [
    'zope.component',
    'sqlalchemy',
    'argparse',
    'alembic',
    'graphviz',
]

setup(
    name="AnyBlok",
    version=version,
    author="Anybox",
    author_email="jssuzanne@anybox.fr",
    description="Anyblok is a dynamic injection blok framework",
    license="GPL",
    long_description='\n'.join((
        open('doc/index.rst').read(),
    )),
    url="https://bitbucket.org/anybox/erpblok",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=requires,
    tests_require=requires + ['nose'],
    classifiers=[
    ],
    entry_points={
        'AnyBlok': [
            'anyblok-core=anyblok.bloks.anyblok_core:AnyBlokCore',
        ],
        'TestAnyBlok': [
            'test-blok1=anyblok.test_bloks.test_blok1:TestBlok',
            'test-blok2=anyblok.test_bloks.test_blok2:TestBlok',
            'test-blok3=anyblok.test_bloks.test_blok3:TestBlok',
            'test-blok4=anyblok.test_bloks.test_blok4:TestBlok',
            'test-blok5=anyblok.test_bloks.test_blok5:TestBlok',
            'test-blok6=anyblok.test_bloks.test_blok6:TestBlok',
        ],
    },
    extras_require={},
)
