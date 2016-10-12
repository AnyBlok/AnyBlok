# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


@Declarations.register(Declarations.Core)
class InstrumentedList:
    """ class of the return of the query.all() or the relationship list
    """

    def __getattr__(self, name):
        if name in ('__emulates__', ):
            return None

        def wrapper(*args, **kwargs):
            return [getattr(x, name)(*args, **kwargs) for x in self]

        if not self:
            return []
        elif hasattr(getattr(self[0], name), '__call__'):
            return wrapper
        else:
            return [getattr(x, name) for x in self]
