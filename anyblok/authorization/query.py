# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Query objects that are rewrapped with permission filtering."""


class QueryWithNoResults:
    """Gives an empty result set without even calling the database

    Useful in cases where the authz system knows beforehand that there won't
    be any result. This can happen for instance if the policy is about the
    model, instead of individual records.
    """

    def count(self):
        return 0

    def all(self):
        return []

    def first(self):
        return None  # TODO exc ?

QUERY_WITH_NO_RESULTS = QueryWithNoResults()


class PostFilteredQuery:
    """Query class returned by the authorization system.

    It takes into account various postfiltering scenarios. Even for cases
    where there is no postfiltering, it's worthwile encapsulate, so that
    downstream code does not rely on methods that would fail if a postfiltering
    policy were to be used.
    """

    def __init__(self, query, postfilters):
        self.query = query
        self.postfilters = postfilters

    def count(self):
        if self.postfilters:
            # TODO add policy information (needs to change __init__)
            raise RuntimeError(
                "Cannot apply count to a permission postfiltered query")
        return self.query.count()

    def filter_one(self, result):
        pfs = self.postfilters
        for rec in result:
            pf = pfs.get(result.__class__)
            if pf is None:
                continue
            if not pf(rec):
                return False

        return True

    def all(self):
        if not self.postfilters:
            return self.query.all()
        return filter(self.filter_one, self.query.all())

    def first(self):
        if not self.postfilters:
            return self.query.first()
        else:
            raise NotImplementedError
