# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from . import release


PROMPT = "%(processName)s - %(version)s"


def start(processName, version=release.version, prompt=PROMPT,
          configuration_groups=None, entry_points=None,
          useseparator=False, loadwithoutmigration=False):
    """ Function which initialize the application

    ::

        registry = start('My application',
                         configuration_groups=['config', 'database'],
                         entry_points=['AnyBlok'])

    :param processName: Name of the application
    :param version: Version of the application
    :param prompt: Prompt message for the help
    :param configuration_groups: list of the group of option for argparse
    :param entry_points: entry point where load blok
    :param useseparator: boolean, indicate if configuration option are split
        betwwen two application
    :param withoutautomigration: if True, any
    :rtype: registry if the database name is in the configuration
    """
    from .blok import BlokManager
    from .config import Configuration
    from .registry import RegistryManager

    description = prompt % {'processName': processName, 'version': version}
    if configuration_groups is not None:
        Configuration.load(description=description,
                           configuration_groups=configuration_groups,
                           useseparator=useseparator)

    if entry_points:
        BlokManager.load(entry_points=entry_points)
    else:
        BlokManager.load()

    db_name = Configuration.get('db_name')
    if not db_name:
        return None

    registry = RegistryManager.get(
        db_name, loadwithoutmigration=loadwithoutmigration)
    registry.commit()
    return registry


BDD = {
}


from .declarations import Declarations  # noqa
from . import databases  # noqa
from . import core  # noqa
from . import model  # noqa
from . import mixin  # noqa
from .authorization import binding  # noqa
from .imp import reload_module_if_blok_is_reloading  # noqa
