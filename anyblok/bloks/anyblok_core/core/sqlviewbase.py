# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.model import ViewException
from .sqlbase import SqlMixin


def query_method(name):

    def wrapper(cls, query, *args, **kwargs):
        raise ViewException("%r.%r method are not availlable on view model" % (
            cls, name))

    return classmethod(wrapper)


@Declarations.register(Declarations.Core)
class SqlViewBase(SqlMixin):
    """ this class is inherited by all the SQL view
    """

    sqlalchemy_query_delete = query_method('delete')
    sqlalchemy_query_update = query_method('update')
