# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.blok import BlokManager
from anyblok.registry import RegistryManager
from anyblok.config import Configuration
from anyblok.environment import EnvironmentManager
from copy import deepcopy


def init_registry_with_bloks(bloks, function, **kwargs):
    if bloks is None:
        bloks = []

    if isinstance(bloks, tuple):
        bloks = list(bloks)

    if 'anyblok-test' not in bloks:
        bloks.append('anyblok-test')

    loaded_bloks = deepcopy(RegistryManager.loaded_bloks)
    if function is not None:
        EnvironmentManager.set('current_blok', 'anyblok-test')
        try:
            function(**kwargs)
        finally:
            EnvironmentManager.set('current_blok', None)

    try:
        registry = RegistryManager.get(
            Configuration.get('db_manager'),
            unittest=False)
        if bloks:
            registry.upgrade(install=bloks)
    finally:
        RegistryManager.loaded_bloks = loaded_bloks

    return registry


@pytest.fixture(scope="module")
def bloks_loaded():
    BlokManager.load()
    yield
    BlokManager.unload()
