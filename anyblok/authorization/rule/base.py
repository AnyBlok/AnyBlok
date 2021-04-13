# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Based definition for authorization policies."""


class RuleNotForModelClasses(Exception):
    """Raised by authorization policies that don't make sense on model classes.

    For instance, if a permission check is done on a model class, and the
    policy associations are made with a policy that needs to check attributes,
    then the association must be corrected.
    """

    def __init__(self, policy, model):
        self.policy = policy
        self.model = model
        self.message = "Rule %r cannot be used on a model class (got %r)" % (
            policy, model)


class AuthorizationRule:
    """Base class to define the interface and provide some helpers"""

    registry = None
    """Set during assembly phase."""

    def is_declaration(self):
        return self.registry is None  # pragma: no cover

    def check(self, target, principals, permission):
        """Check that one of the principals has permisson on given record.

        :param target: model instance (record) or class. Checking a permission
                       on a model class with a policy that is designed to work
                       on records is considered a configuration error,
                       expressed by :exc:`RuleNotForModelClasses`.
        :param principals: list, set or tuple of strings
        :rtype: bool

        Must be implemented by concrete subclasses.
        """
        raise NotImplementedError  # pragma: no cover

    def filter(self, model, query, principals, permission):
        """Return a new query with added permission filtering.

        Must be implemented by concrete subclasses.

        :param query: the :class:`Query` instance to modify to express
                      the permission for these principals.
        :param model: the model on which the policy is applied
        :rtype: :class:`Query`)

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
        raise NotImplementedError  # pragma: no cover

    postfilter = None
    """Filter by permission records obtained by a filtered query.

    By default, this is ``None``, to indicate that the policy does not perform
    any post filtering, but concrete policies can implement
    a method with the following signature::

        def postfilter(self, record, principals, permission):

    Such implementations can (and usually, for performance, should) assume
    that the query that produced the records was a filtered one.

    The purpose of using the explicit ``None`` marker is to permit some calls
    that don't make sense on a postfiltered operation (such as ``count()``).
    """


class DenyAll(AuthorizationRule):

    def check(self, *args):
        return False  # pragma: no cover

    def filter(self, *args):
        return False  # pragma: no cover


deny_all = DenyAll
