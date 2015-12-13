# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import Integer, Selection, String


@Declarations.register(Declarations.Mixin)
class IOMixin:

    id = Integer(primary_key=True)
    mode = Selection(selections="get_mode_choices", nullable=False)
    model = String(foreign_key=Declarations.Model.System.Model.use('name'),
                   nullable=False)

    @classmethod
    def get_mode_choices(cls):
        return {}

    def get_formater(self, ctype):
        formater_name = 'Model.IO.Formater.' + ctype
        if self.registry.has(formater_name):
            return self.registry.get(formater_name)()
        else:
            return self.registry.IO.Formater()
