# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Authorization subframework.

The founding principle of authorization handling within Anyblok is to check
authorization explicitely at the edge of the system (for instance,
for applications
exposed over HTTP, that would be in the controllers), because that is where the
idea of user, or slightly more generally, has functional semantics that can
be interpreted in the context of a given action.

In that spirit, we don't pass the user to the core framework and business
layers.
Instead, these provide *policies* to check permissions on records or query
records according to the.

The declarations at the edge will *associate* the policies with the
models. The edge user-aware methods will call the check and query facilities
provided by the core that themselves apply the relevant policies.
"""
from .declarations import Declarations
from .environment import EnvironmentManager
from .registry import RegistryManager


@Declarations.add_declaration_type(isAnEntry=True,
                                   assemble='assemble_callback')
class AuthorizationPolicyAssociation:
    """Encodes which policy to use per model or permission."""

    def __new__(cls, model_declaration, policy, permission=None):
        """Declare for given model than policy should be used.

        :param permission: if provided, the policy will apply for this
                           permission only, otherwise, it will act as the
                           default policy for this model.
        """
        cb = EnvironmentManager.get('current_blok')
        model = model_declaration.__registry_name__
        key = (model, permission) if permission is not None else model
        blok_declarations = RegistryManager.loaded_bloks[cb][cls.__name__]
        blok_declarations[key] = policy

    @classmethod
    def assemble_callback(cls, registry):
        registry._authnz_policies = {}
        for blok in registry.ordered_loaded_bloks:
            registry._authnz_policies.update(
                RegistryManager.loaded_bloks[blok][cls.__name__])


class PolicyNotForModelClasses(Exception):
    """Raised by authorization policies that don't make sense on model classes.

    For instance, if a permission check is done on a model class, and the
    policy associations are made with a policy that needs to check attributes,
    then the association must be corrected.
    """

    def __init__(self, policy, model):
        self.policy = policy
        self.model = model
        self.message = "Policy %r cannot be used on a model class (got %r)" % (
            policy, model)


class AuthorizationPolicy:
    """Base class to define the interface and provide some helpers"""

    def check(self, target, principals, permission):
        """Check that one of the principals has permisson on given record.

        :param target: model instance (record) or class. Checking a permission
                       on a model class with a policy that is designed to work
                       on records is considered a configuration error,
                       expressed by :exc:`PolicyNotForModelClasses`.
        :param principals: list, set or tuple of strings
        :rtype: bool

        Must be implemented by concrete subclasses.
        """
        raise NotImplementedError

    def filter(self, query, principals, permission):
        """Return a new query with added permission filtering.

        Must be implemented by concrete subclasses.

        :param query: the query to add permission to
        :rtype: modified query

        It's not necessary that the resulting query expresses fully
        the permission check: this can be complemented if needed
        by postfiltering, notably for conditions that can't be expressed
        conveniently in SQL.

        That being said, if the policy can be expressed totally by query,
        alteration, it's usually the best choice, as it keeps database traffic
        at the lowest.

        The policy also has the possibility to return False, for flat denial
        without even querying the server. That may prove useful in some cases.
        """
        raise NotImplementedError

    def postfilter(self, records, principals, permission):
        """Filter by permission records obtained by a filtered query.

        Implementation can (and usually, for performance, should) assume
        that the query that produced the records was a filtered one.

        The default implementation is to keep all records
        """
        return records


class ModelBasedAuthorizationPolicy(AuthorizationPolicy):
    """Policy to grant authorization uniformly for all records of one model.

    The grants are themselves stored using a model
    """

    def __init__(self, grant_by=None):
        """.

        :params: grant_by is a model declaration
        """
        if grant_by is not None:
            self.grant_model_name = grant_by.__registry_name__
        else:
            self.grant_model_name = 'Model.Authorization.ModelPermissionGrant'

    @property
    def grant_model(self):
        return self.registry.get(self.grant_model_name)

    def _check_on_model(self, model, principals, permission):
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


class DenyAll(AuthorizationPolicy):

    def check(self, *args):
        return False

    def filter(self, *args):
        return False

deny_all = DenyAll
