# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.orm.session import object_state
from .exceptions import (
    ForbidUpdateException, ForbidDeleteException)
from anyblok import Declarations
from anyblok.common import anyblok_column_prefix

Mixin = Declarations.Mixin


@Declarations.register(Mixin)
class ForbidUpdate:

    def get_modified_fields(self):
        state = object_state(self)
        modified_fields = []
        for attr in state.manager.attributes:
            if not hasattr(attr.impl, 'get_history'):
                continue

        added, unmodified, deleted = attr.impl.get_history(
            state, state.dict)

        if added or deleted:
            field = attr.key
            if field.startswith(anyblok_column_prefix):
                field = field[len(anyblok_column_prefix):]

            modified_fields.append(field)

        return modified_fields

    @classmethod
    def before_update_orm_event(cls, mapper, connection, target):
        modified_fields = target.get_modified_fields()
        raise ForbidUpdateException(
            "The modification of %r on %s with field(s) %r is forbidden" % (
                target, cls.__registry_name__, modified_fields))


@Declarations.register(Mixin)
class ForbidDelete:

    @classmethod
    def before_delete_orm_event(cls, mapper, connection, target):
        raise ForbidDeleteException(
            "The deletion of %r on %r is forbidden" % (
                target, cls.__registry_name__))


@Declarations.register(Declarations.Mixin)
class ReadOnly(Mixin.ForbidUpdate, Mixin.ForbidDelete):
    pass
