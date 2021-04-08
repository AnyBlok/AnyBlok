# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Per model flat access rule, based on a Model (table)"""
from anyblok.registry import RegistryManagerException
from .base import AuthorizationRule


class ModelAccessRule(AuthorizationRule):
    """Rule to grant authorization uniformly for all records of one model.

    The grants are themselves stored using a model class, that's provided
    in this blok. The users don't need to install the blok to use this class,
    provided they pass the model class to be used in all cases.
    """

    grant_model_name = 'Model.Authorization.ModelPermissionGrant'

    def __init__(self, grant_model=None):
        """.

        :params: grant_model is a model declaration, that has the needed
                 columns (model, principal, permission)
        """
        if grant_model is not None:  # pragma: no cover
            self.grant_model_name = grant_model.__registry_name__

    @property
    def grant_model(self):
        try:
            return self.registry.get(self.grant_model_name)
        except RegistryManagerException:  # pragma: no cover
            cls = self.__class__
            if self.grant_model_name is not cls.grant_model_name:
                raise
            raise RuntimeError(
                "To use %s with no explicit Grant "
                "model, you must install the model_access blok, "
                "that provides the default %r" % (
                    cls.__name__,
                    cls.grant_model_name))

    def check_on_model(self, model, principals, permission):
        Grant = self.grant_model
        return bool(Grant.query().filter(
            Grant.model == model,
            Grant.principal.in_(principals),
            Grant.permission == permission).limit(1).count())

    def check(self, record, principals, permission):
        return self.check_on_model(record.__registry_name__,
                                   principals,
                                   permission)

    def filter(self, model, query, principals, permission):
        if self.check_on_model(model.__registry_name__,
                               principals, permission):
            return query
        return False
