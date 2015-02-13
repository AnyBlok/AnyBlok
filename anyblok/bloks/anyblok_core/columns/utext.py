# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.types import UnicodeText
from anyblok import Declarations


@Declarations.register(Declarations.Column)
class uText(Declarations.Column):
    """ Unicode text column

    ::

        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        uText = Declarations.Column.uText

        @register(Model)
        class Test:

            x = uText(default=u'test')

    """
    sqlalchemy_type = UnicodeText
