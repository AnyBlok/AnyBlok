# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import release
from anyblok.blok import Blok


class ModelBasedAuthorizationBlok(Blok):
    version = release.version
    author = "Suzanne Jean-Sébastien"
    logo = "../anyblok-logo_alpha_256.png"

    @classmethod
    def import_declaration_module(cls):
        from . import models  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import models

        reload(models)
