# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok
from anyblok.release import version


class AnyBlokIO(Blok):
    """
    In / Out tool's:

    * Formater: convert value 2 str or str 2 value in function of the field,
    * Importer: main model to define an import,
    * Exporter: main model to define an export,
    """
    version = version

    required = [
        'anyblok-core',
    ]

    @classmethod
    def declare_io(cls):
        from anyblok import Declarations

        @Declarations.register(Declarations.Model)
        class IO:
            pass

    @classmethod
    def import_declaration_module(cls):
        cls.declare_io()
        from . import mapping  # noqa
        from . import mixin  # noqa
        from . import importer  # noqa
        from . import exporter  # noqa
        from . import formater  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        cls.declare_io()
        from . import mapping
        reload(mapping)
        from . import mixin
        reload(mixin)
        from . import importer
        reload(importer)
        from . import exporter
        reload(exporter)
        from . import formater
        reload(formater)
