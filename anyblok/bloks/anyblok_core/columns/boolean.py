# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import Boolean as SA_Boolean
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class Boolean(Declarations.Column):
    """ Boolean column

    ::

        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        Boolean = Declarations.Column.Boolean

        @register(Model)
        class Test:

            x = Boolean(default=True)

    """
    sqlalchemy_type = SA_Boolean
