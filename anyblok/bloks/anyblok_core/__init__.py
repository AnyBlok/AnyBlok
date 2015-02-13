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
    known models, fields, columns and relationships:

    * Core model
    * Field Type
        - Function
    * Column Types:
        - DateTime
        - Decimal
        - Float
        - Time
        - BigInteger
        - Boolean
        - Date
        - Integer
        - Interval
        - LargeBinary
        - SmallInteger
        - String
        - Text
        - uString
        - uText
        - Selection
        - Json
    * Relationship types
        - One2One
        - Many2One
        - One2Many
        - Many2Many
    * System Models
        - Blok
        - Model
        - Field
        - Column
        - Relationship
    """

    version = version
    autoinstall = True
    priority = 0

    @classmethod
    def import_declaration_module(cls):
        from . import fields  # noqa
        from . import columns  # noqa
        from . import relationship  # noqa
        from . import core  # noqa
        from . import system  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import fields
        reload(fields)
        from . import columns
        reload(columns)
        from . import relationship
        reload(relationship)
        from . import core
        reload(core)
        from . import system
        reload(system)
