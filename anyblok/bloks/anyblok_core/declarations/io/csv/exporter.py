# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
register = Declarations.register
IO = Declarations.Model.IO
Mixin = Declarations.Mixin
Integer = Declarations.Column.Integer
One2Many = Declarations.RelationShip.One2Many


@register(IO.Exporter)
class Field(Mixin.IOCSVFieldMixin):

    exporter = Integer(foreign_key=(IO.Exporter, 'id'), nullable=False)


@register(IO)
class Exporter(Mixin.IOCSVMixin):

    fields_to_export = One2Many(model=IO.Exporter.Field)
