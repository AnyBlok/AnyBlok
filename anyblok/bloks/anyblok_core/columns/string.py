# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import String as SA_String
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class String(Declarations.Column):
    """ String column

    ::

        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        String = Declarations.Column.String

        @register(Model)
        class Test:

            x = String(default='test')

    """
    def __init__(self, *args, **kwargs):
        size = 64
        if 'size' in kwargs:
            size = kwargs.pop('size')

        self.sqlalchemy_type = SA_String(size)

        super(String, self).__init__(*args, **kwargs)
