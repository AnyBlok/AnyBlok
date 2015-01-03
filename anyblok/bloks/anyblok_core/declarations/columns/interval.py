# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import Interval as SA_Interval
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class Interval(Declarations.Column):
    """ Datetime interval column

    ::

        from datetime import timedelta
        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        Interval = Declarations.Column.Interval

        @register(Model)
        class Test:

            x = Interval(default=timedelta(days=5))

    """
    sqlalchemy_type = SA_Interval
