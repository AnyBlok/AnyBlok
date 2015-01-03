# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import Unicode
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class uString(Declarations.Column):
    """ Unicode column

    ::

        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        uString = Declarations.Column.uString

        @register(Model)
        class Test:

            x = uString(de", default=u'test')

    """
    def __init__(self, *args, **kwargs):
        size = 64
        if 'size' in kwargs:
            size = kwargs.pop('size')

        self.sqlalchemy_type = Unicode(size)

        super(uString, self).__init__(*args, **kwargs)
