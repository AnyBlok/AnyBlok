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
          argsparse_groups=None, entry_points=None,
          useseparator=False):
    """ Function which initialize the application

    ::

        registry = start('My application',
                         argsparse_groups=['config', 'database'],
                         entry_points=['AnyBlok'])

    :param processName: Name of the application
    :param version: Version of the application
    :param prompt: Prompt message for the help
    :param argsparse_groups: list of the group of option for argparse
    :param entry_points: entry point where load blok
    :param useseparator: boolean, indicate if argsparse option are split
        betwwen two application
    :rtype: registry if the database name is in the configuration
    """
    from .blok import BlokManager
    from ._argsparse import ArgsParseManager
    from .registry import RegistryManager

    if entry_points:
        BlokManager.load(entry_points=entry_points)
    else:
        BlokManager.load()

    description = prompt % {'processName': processName, 'version': version}
    if argsparse_groups is not None:
        ArgsParseManager.load(description=description,
                              argsparse_groups=argsparse_groups,
                              useseparator=useseparator)

    dbname = ArgsParseManager.get('dbname')
    if not dbname:
        return None

    registry = RegistryManager.get(dbname)
    registry.commit()
    return registry


BDD = {
}


from .declarations import Declarations  # noqa
from . import exception  # noqa
from . import databases  # noqa
from . import core  # noqa
from . import field  # noqa
from . import column  # noqa
from . import relationship  # noqa
from . import model  # noqa
from . import mixin  # noqa
from . import authorization  # noqa
from ._imp import reload_module_if_blok_is_reloaded  # noqa
