# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import BigInteger as SA_BigInteger
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class BigInteger(Declarations.Column):
    """ Big integer column

    ::

        from AnyBlok import register, Model
        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        BigInteger = Declarations.Column.BigInteger

        @register(Model)
        class Test:

            x = BigInteger(default=1)

    """
    sqlalchemy_type = SA_BigInteger
