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
Many2One = Declarations.RelationShip.Many2One


@register(IO)
class Exporter(Mixin.IOCSVMixin):
    pass


@register(IO.Exporter)
class Field(Mixin.IOCSVFieldMixin):

    exporter = Many2One(model=IO.Exporter, nullable=False,
                        one2many='fields_to_export')
