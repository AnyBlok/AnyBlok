# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.orm import Session as SA_Session
from anyblok import Declarations
from sqlalchemy.orm.decl_api import DeclarativeMeta


@Declarations.register(Declarations.Core)
class Session(SA_Session):
    """ Overload of the SqlAlchemy session
    """

    def __init__(self, *args, **kwargs):
        kwargs['query_cls'] = self.registry_query
        super(Session, self).__init__(*args, **kwargs)

    def get_bind(self, bind=None, mapper=None, clause=None, **kwargs):
        if mapper is not None:
            return mapper.class_.get_bind()
        if clause is not None and hasattr(clause, 'Model'):
            return self.anyblok.get(clause.Model).get_bind()
        if self._flushing and bind and isinstance(bind.class_, DeclarativeMeta):
            return bind.class_.get_bind()
        if bind:
            return bind

        return self.anyblok.named_binds['main']
