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
    'sqlalchemy >= 0.8.3',
    'argparse',
    'nose',
]

setup(
    name="AnyBlok",
    version=version,
    author="Anybox",
    author_email="jssuzanne@anybox.fr",
    description="Anyblok is a dynamic injection blok framework",
    license="GPL",
    long_description='\n'.join((
        open('index.rst').read(),
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
        'console_scripts': [
            'anyblok_createdb=anyblok.scripts:createdb',
        ],
        'AnyBlok': [
            'anyblok-core=bloks.anyblokcore:AnyBlokCore',
        ],
    },
    extras_require={},
)
