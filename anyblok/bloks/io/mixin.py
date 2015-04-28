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
String = Declarations.Column.String


@Declarations.register(Declarations.Mixin)
class IOMixin:

    id = Integer(primary_key=True)
    check = Boolean(default=False)
    mode = Selection(selections="get_mode_choices", nullable=False)
    model = String(foreign_key=(Declarations.Model.System.Model, 'name'),
                   nullable=False)

    @classmethod
    def get_mode_choices(cls):
        return {}
