# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
register = Declarations.register
Mixin = Declarations.Mixin
String = Declarations.Column.String
Integer = Declarations.Column.Integer


@register(Mixin)
class IOCSVFieldMixin:

    id = Integer(primary_key=True)
    name = String(nullable=False)


@register(Mixin)
class IOCSVMixin:

    csv_model = String(foreign_key=(Declarations.Model.System.Model, 'name'))
    csv_delimiter = String(nullable=False, default=",")

    @classmethod
    def get_mode_choices(cls):
        res = super(IOCSVMixin, cls).get_mode_choices()
        res[cls.__registry_name__] = 'CSV'
        return res
