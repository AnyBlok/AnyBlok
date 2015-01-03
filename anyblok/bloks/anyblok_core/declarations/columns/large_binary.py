# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import LargeBinary as SA_LargeBinary
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class LargeBinary(Declarations.Column):
    """ Large binary column

    ::

        from os import urandom
        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        LargeBinary = Declarations.Column.LargeBinary

        blob = urandom(100000)

        @register(Model)
        class Test:

            x = LargeBinary(default=blob)

    """
    sqlalchemy_type = SA_LargeBinary
