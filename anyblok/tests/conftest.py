# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import logging
from copy import deepcopy
import pytest
from anyblok.testing import sgdb_in
from anyblok.blok import BlokManager
from anyblok.config import Configuration
from anyblok.environment import EnvironmentManager
from anyblok.registry import RegistryManager
from sqlalchemy_utils.functions import (
    drop_database, database_exists, create_database)

logger = logging.getLogger(__name__)


def init_registry_with_bloks(bloks, function, **kwargs):
    if bloks is None:
        bloks = []
    if isinstance(bloks, tuple):
        bloks = list(bloks)
    if isinstance(bloks, str):
        bloks = [bloks]

    anyblok_test_name = 'anyblok-test'
    if anyblok_test_name not in bloks:
        bloks.append(anyblok_test_name)

    loaded_bloks = deepcopy(RegistryManager.loaded_bloks)
    if function is not None:
        EnvironmentManager.set('current_blok', anyblok_test_name)
        try:
            function(**kwargs)
        finally:
            EnvironmentManager.set('current_blok', None)
    try:
        registry = RegistryManager.get(
            Configuration.get('db_name'),
            unittest=True)

        # update required blok
        registry_bloks = registry.get_bloks_by_states('installed', 'toinstall')
        toinstall = [x for x in bloks if x not in registry_bloks]
        toupdate = [x for x in bloks if x in registry_bloks]
        registry.upgrade(install=toinstall, update=toupdate)
    finally:
        RegistryManager.loaded_bloks = loaded_bloks

    return registry


def init_registry(function, **kwargs):
    return init_registry_with_bloks([], function, **kwargs)


@pytest.fixture(scope="session")
def base_loaded(request, configuration_loaded):
    if sgdb_in(['MySQL', 'MariaDB']):
        return

    url = Configuration.get('get_url')()
    if not database_exists(url):
        db_template_name = Configuration.get('db_template_name', None)
        create_database(url, template=db_template_name)

    BlokManager.load()
    registry = init_registry_with_bloks([], None)
    registry.commit()
    registry.close()
    BlokManager.unload()


@pytest.fixture(scope="module")
def bloks_loaded(request, base_loaded):
    request.addfinalizer(BlokManager.unload)
    BlokManager.load()


@pytest.fixture(scope="module")
def testbloks_loaded(request, base_loaded):
    request.addfinalizer(BlokManager.unload)
    BlokManager.load(entry_points=('bloks', 'test_bloks'))


def reset_db():
    if sgdb_in(['MySQL', 'MariaDB']):
        url = Configuration.get('get_url')()
        if database_exists(url):
            drop_database(url)

        db_template_name = Configuration.get('db_template_name', None)
        create_database(url, template=db_template_name)


@pytest.fixture(scope="class")
def registry_blok(request, bloks_loaded):
    reset_db()
    registry = init_registry_with_bloks([], None)
    request.addfinalizer(registry.close)
    return registry


@pytest.fixture(scope="class")
def registry_testblok(request, testbloks_loaded):
    reset_db()
    registry = init_registry_with_bloks([], None)
    request.addfinalizer(registry.close)
    return registry


@pytest.fixture(scope="function")
def registry_testblok_func(request, testbloks_loaded):
    reset_db()
    registry = init_registry_with_bloks([], None)
    request.addfinalizer(registry.close)
    return registry


@pytest.fixture(
    scope="class",
    params=[
        ('prefix', 'suffix'),
        ('', ''),
    ]
)
def db_schema(request, bloks_loaded):
    Configuration.set('prefix_db_schema.Model.*', request.param[0])
    Configuration.set('suffix_db_schema.Model.*', request.param[1])

    def rollback():
        Configuration.set('prefix_db_schema.Model.*', '')
        Configuration.set('suffix_db_schema.Model.*', '')

    request.addfinalizer(rollback)
