# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pkg_resources import iter_entry_points
from logging import getLogger
logger = getLogger(__name__)


def load_init_function_from_entry_points(unittest=False):
    """Call all the entry point ``anyblok_pyramid.init`` to update
    the argument setting

    the callable need to have one parametter, it is a dict::

        def init_function(unittest=False):
            ...

    We add the entry point by the setup file::

        setup(
            ...,
            entry_points={
                'anyblok.init': [
                    init_function=path:init_function,
                    ...
                ],
            },
            ...,
        )


    """
    for i in iter_entry_points('anyblok.init'):
        print('AnyBlok Load init: %r' % i)
        i.load()(unittest=unittest)


def configuration_post_load(unittest=False):
    """Call all the entry point ``anyblok_configuration.post_load`` to
    initialize some service in function of the configuration

    the callable need to have one parametter, it is a dict::

        def post_load_function(unittest=False):
            ...

    We add the entry point by the setup file::

        setup(
            ...,
            entry_points={
                'anyblok_configuration.post_load': [
                    post_load_function=path:post_load_function,
                    ...
                ],
            },
            ...,
        )


    """
    for i in iter_entry_points('anyblok_configuration.post_load'):
        logger.info('AnyBlok configuration post load: %r' % i)
        i.load()(unittest=unittest)


def start(processName, entry_points=None,
          useseparator=False, loadwithoutmigration=False, config=None,
          **kwargs):
    """ Function which initialize the application

    ::

        registry = start('My application',
                         entry_points=['AnyBlok'])

    :param processName: Name of the application
    :param version: Version of the application
    :param prompt: Prompt message for the help
    :param entry_points: entry point where load blok
    :param useseparator: boolean, indicate if configuration option are split
        betwwen two application
    :param loadwithoutmigration: if True, any migration operation will do
    :rtype: registry if the database name is in the configuration
    """
    from .blok import BlokManager
    from .config import Configuration
    from .registry import RegistryManager

    load_init_function_from_entry_points()
    if config is None:
        config = {}

    Configuration.load(processName,
                       useseparator=useseparator, **config)

    configuration_post_load()
    if entry_points:
        BlokManager.load(entry_points=entry_points)
    else:
        BlokManager.load()

    db_name = Configuration.get('db_name')
    logger.debug("start(): db_name=%r", db_name)
    if not db_name:
        logger.warning("start(): no database name in configuration, "
                       "bailing out")
        return None

    registry = RegistryManager.get(
        db_name, loadwithoutmigration=loadwithoutmigration, **kwargs)
    registry.commit()
    return registry


from .declarations import Declarations  # noqa
from . import core  # noqa
from . import model  # noqa
from . import mixin  # noqa
from .authorization import binding  # noqa
from .imp import reload_module_if_blok_is_reloading  # noqa
