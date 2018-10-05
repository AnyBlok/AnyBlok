import logging

import pytest
from anyblok.blok import BlokManager
from anyblok.registry import RegistryManager
from anyblok.config import Configuration
from anyblok.environment import EnvironmentManager
from copy import deepcopy

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
            Configuration.get('db_manager'),
            unittest=False)

        # update required blok
        registry_bloks = registry.get_bloks_by_states('installed', 'toinstall')
        if bloks:
            for blok_to_install in bloks:
                if blok_to_install not in registry_bloks:
                    registry.upgrade(install=[blok_to_install])
                else:
                    registry.upgrade(update=[blok_to_install])
    finally:
        RegistryManager.loaded_bloks = loaded_bloks

    return registry


@pytest.fixture(scope="module")
def bloks_loaded():
    BlokManager.load()
    yield
    BlokManager.unload()
