# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
Integer = Declarations.Column.Integer
LargeBinary = Declarations.Column.LargeBinary
Boolean = Declarations.Column.Boolean
Selection = Declarations.Column.Selection


@Declarations.register(Declarations.Mixin)
class IOMixin:

    id = Integer(primary_key=True)
    file = LargeBinary()
    offset = Integer(nullable=False, default=0)
    nb_grouped_line = Integer(nullable=False, default=50)
    check = Boolean(default=False)
    mode = Selection(selections="get_mode_choices", nullable=False)

    @classmethod
    def get_mode_choices(cls):
        return {}

    def run(self):
        return self.get_model(self.mode)(self).run()
