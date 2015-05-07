# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok, BlokManager
from anyblok.release import version


class AnyBlokIOCSV(Blok):
    """ CSV Importer / Exporter behaviour
    """
    version = version

    required = [
        'anyblok-io',
    ]

    @classmethod
    def import_declaration_module(cls):
        from . import mixin  # noqa
        from . import importer  # noqa
        from . import exporter  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import mixin
        reload(mixin)
        from . import importer
        reload(importer)
        from . import exporter
        reload(exporter)

    def update(self, latest_version):
        super(AnyBlokIOCSV, self).update(latest_version)
        if not BlokManager.has_importer('csv'):
            BlokManager.add_importer('csv', 'Model.IO.Importer.CSV')

    def uninstall(self):
        super(AnyBlokIOCSV, self).uninstall()
        BlokManager.remove_importer('csv')
