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
    version = version

    required = [
        'anyblok-core',
    ]

    @classmethod
    def declare_io(cls):
        from anyblok import Declarations
        register = Declarations.register
        Model = Declarations.Model

        @register(Declarations.Exception)
        class IOException(Exception):
            """ IO exception """

        @register(Model)
        class IO:
            pass

    @classmethod
    def import_declaration_module(cls):
        cls.declare_io()
        from . import mapping  # noqa
        from . import mixin  # noqa
        from . import importer  # noqa
        from . import exporter  # noqa

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
