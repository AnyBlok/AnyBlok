# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.orm import Session as SA_Session
from anyblok import Declarations


@Declarations.register(Declarations.Core)
class Session(SA_Session):
    """ Overload of the SqlAlchemy session
    """

    def __init__(self, *args, **kwargs):
        kwargs['query_cls'] = self.registry_query
        super(Session, self).__init__(*args, **kwargs)

    def get_bind(self, mapper=None, clause=None, **kwargs):
        try:
            return super(Session, self).get_bind(
                mapper=mapper, clause=clause, **kwargs)
        except Exception:
            if mapper is not None:
                return mapper.class_.get_engine()
            elif clause is not None:
                return self.anyblok.get(clause.Model).get_engine()
