# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .exceptions import (
    ForbidUpdateException, ForbidDeleteException)
from anyblok import Declarations
from anyblok.column import Boolean, Selection

Mixin = Declarations.Mixin


@Declarations.register(Mixin)
class ForbidUpdate:

    @classmethod
    def before_update_orm_event(cls, mapper, connection, target):
        modified_fields = target.get_modified_fields()
        raise ForbidUpdateException(
            "The modification of %r on %s with field(s) %r is forbidden" % (
                target, cls.__registry_name__, modified_fields.keys()))


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


@Declarations.register(Mixin)
class ConditionalForbidUpdate:

    def check_if_forbid_update_condition_is_true(self, **previous_values):
        raise ForbidUpdateException(
            "No 'check_if_forbid_update_condition_is_true' method found "
            " on %s to check the allow or forbid choice " % (
                self.__registry_name__))

    @classmethod
    def before_update_orm_event(cls, mapper, connection, target):
        modified_fields = target.get_modified_fields()
        if target.check_if_forbid_update_condition_is_true(**modified_fields):
            raise ForbidUpdateException(
                "The modification of %r on %s with field(s) %r is forbidden" % (
                    target, cls.__registry_name__, modified_fields.keys()))


@Declarations.register(Mixin)
class ConditionalForbidDelete:

    def check_if_forbid_delete_condition_is_true(self):
        raise ForbidDeleteException(
            "No 'check_if_forbid_delete_condition_is_true' method found "
            " on %s to check the allow or forbid choice " % (
                self.__registry_name__))

    @classmethod
    def before_delete_orm_event(cls, mapper, connection, target):
        if target.check_if_forbid_delete_condition_is_true():
            raise ForbidDeleteException(
                "The deletion of %r on %r is forbidden" % (
                    target, cls.__registry_name__))


@Declarations.register(Declarations.Mixin)
class ConditionalReadOnly(Mixin.ConditionalForbidUpdate,
                          Mixin.ConditionalForbidDelete):
    pass


@Declarations.register(Declarations.Mixin)
class BooleanForbidUpdate(Mixin.ConditionalForbidUpdate):

    forbid_update = Boolean(default=False)

    def check_if_forbid_update_condition_is_true(self, **previous_values):
        return previous_values.get('forbid_update', self.forbid_update)


@Declarations.register(Declarations.Mixin)
class BooleanForbidDelete(Mixin.ConditionalForbidDelete):

    forbid_delete = Boolean(default=False)

    def check_if_forbid_delete_condition_is_true(self):
        return self.forbid_delete


@Declarations.register(Declarations.Mixin)
class BooleanReadOnly(Mixin.ConditionalForbidUpdate,
                      Mixin.ConditionalForbidDelete):

    readonly = Boolean(default=False)

    def check_if_forbid_update_condition_is_true(self, **previous_values):
        return previous_values.get('readonly', self.readonly)

    def check_if_forbid_delete_condition_is_true(self):
        return self.readonly


@Declarations.register(Declarations.Mixin)
class StateReadOnly(Mixin.ConditionalForbidUpdate,
                    Mixin.ConditionalForbidDelete):
    DEFAULT_STATE = None

    state = Selection(selections='get_states',
                      default='get_default_state',
                      nullable=False)

    @classmethod
    def get_default_state(cls):
        return cls.DEFAULT_STATE

    @classmethod
    def get_states(cls):
        return {}
