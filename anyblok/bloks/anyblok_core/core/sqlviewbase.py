# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.model.exceptions import ViewException
from .sqlbase import SqlMixin


@Declarations.register(Declarations.Core)
class SqlViewBase(SqlMixin):
    """ this class is inherited by all the SQL view
    """

    def update(self, *args, **kwargs):
        raise ViewException(  # pragma: no cover
            "%r.update method are not availlable on view "
            "model" % self.__registry_name__)

    def delete(self, *args, **kwargs):
        raise ViewException(  # pragma: no cover
            "%r.delete method are not availlable on view "
            "model" % self.__registry_name__)
