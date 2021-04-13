# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .base import AuthorizationRule
from .base import RuleNotForModelClasses


class AttributeAccessRule(AuthorizationRule):
    """Grant authorization to principals coinciding with a record attribute.

    Whatever the permission is associated to this policy, it will be granted
    to principals on records whose attribute is equal to the principal.

    A common use-case is to associate it to a precise permission, in
    conjunction with a flatter default policy, such as
    :class:`..model_authz.ModelBasedAutorizationRule`
    """

    def __init__(self, attr, model_rule=None):
        """.

        :param attr: The attribute that is being compared with principal.
        :param model_rule: If set, checks done on model classes will be
                           relayed to this other rule. Otherwise, the
                           standard exception that the rule does not apply
                           to model classes is raised.

        The ``model_rule`` allows to express conveniently that some
        principal has a "general" Read right on some model,
        while still allowing it to read only some of the
        records, and to protect the querying by the same
        'Read' permission. Similar and finer effects can
        be obtained by creating a separate 'Search' permission, but that may
        not be appropriate in a given context.
        """
        self.attr = attr
        self.model_rule = model_rule

        self._registry = None

    @property
    def registry(self):
        """On this rule, we'll need a setter for registry"""
        return self._registry  # pragma: no cover

    @registry.setter
    def registry(self, registry):
        """Apply registry also to model_rule if needed"""
        self._registry = registry
        if self.model_rule is not None:
            self.model_rule.registry = registry

    def check(self, record, principals, permission):
        if isinstance(record, type):
            if self.model_rule is not None:
                return self.model_rule.check(record, principals, permission)
            raise RuleNotForModelClasses(self, record)

        return getattr(record, self.attr) in principals

    def filter(self, model, query, principals, permission):
        return query.filter(getattr(model, self.attr).in_(principals))
