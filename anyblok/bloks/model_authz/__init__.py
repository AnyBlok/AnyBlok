# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok
from anyblok import release
from anyblok.authorization import AuthorizationPolicy
from anyblok.registry import RegistryManagerException


class ModelBasedAuthorizationBlok(Blok):

    version = release.version

    @classmethod
    def import_declaration_module(cls):
        from . import models  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import models
        reload(models)


class ModelBasedAuthorizationPolicy(AuthorizationPolicy):
    """Policy to grant authorization uniformly for all records of one model.

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
        if grant_model is not None:
            self.grant_model_name = grant_model.__registry_name__

    @property
    def grant_model(self):
        try:
            return self.registry.get(self.grant_model_name)
        except RegistryManagerException:
            cls = self.__class__
            if self.grant_model_name is not cls.grant_model_name:
                raise
            raise RuntimeError(
                "To use %s with no explicit Grant "
                "model, you must install the %s blok, "
                "that provides a default one" % (
                    cls.__name__,
                    ModelBasedAuthorizationBlok.__name__))

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

    def filter(self, query, principals, permission):
        model = self.query.get_model().__registry_name__

        if self._check_on_model(model, principals, permission):
            return query
        return False
