# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import Float as SA_Float
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class Float(Declarations.Column):
    """ Float column

    ::

        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        Float = Declarations.Column.Float

        @register(Model)
        class Test:

            x = Float(default=1.0)

    """
    sqlalchemy_type = SA_Float
