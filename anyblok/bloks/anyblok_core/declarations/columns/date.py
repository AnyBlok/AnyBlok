# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import Date as SA_Date
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class Date(Declarations.Column):
    """ Date column

    ::

        from datetime import date
        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        Date = Declarations.Column.Date

        @register(Model)
        class Test:

            x = Date(default=date.today())

    """
    sqlalchemy_type = SA_Date
