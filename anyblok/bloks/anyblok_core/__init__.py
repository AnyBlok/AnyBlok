# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok
from anyblok.release import version


class AnyBlokCore(Blok):
    """
    This blok is required by all anyblok application. This blok define the main
    fonctionnality to install, update and uninstall blok. And also list the
    known models, fields, columns and relationships
    """

    version = version
    autoinstall = True
    priority = 0

    @classmethod
    def import_declaration_module(cls):
        from . import core  # noqa
        from . import system  # noqa
        from . import authorization  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import core
        reload(core)
        from . import system
        reload(system)
        from . import authorization
        reload(authorization)
