# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok
from anyblok import release
from anyblok.authorization.policy import AuthorizationPolicy
from anyblok.authorization.policy import PolicyNotForModelClasses


class AttributeBasedAuthorization(Blok):

    version = release.version


class AttributeBasedAuthorizationPolicy(AuthorizationPolicy):
    """Grant authorization to principals coinciding with a record attribute.

    Whatever the permission is associated to this policy, it will be granted
    to principals on records whose attribute is equal to the principal.

    A common use-case is to associate it to a precise permission, in
    conjunction with a flatter default policy, such as
    :class:`..model_authz.ModelBasedAutorizationPolicy`
    """

    def __init__(self, attr):
        """.

        :param attr: The attribute that is being compared with principal.
        """
        self.attr = attr

    def check(self, record, principals, permission):
        if hasattr(record, '__name__'):
            raise PolicyNotForModelClasses(self, record)
        return getattr(record, self.attr) in principals

    def filter(self, model, query, principals, permission):
        return query.filter(getattr(model, self.attr).in_(principals))
