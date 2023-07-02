# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest


@pytest.mark.usefixtures("rollback_registry")
class TestQueryScope:
    def test_dictone(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Cache.query().limit(1)
        cache = query.one()
        assert query.dictone() == {
            "id": cache.id,
            "method": cache.method,
            "registry_name": cache.registry_name,
        }

    def test_iteration(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Blok.query()
        has_iteration = False
        for blok in query:
            has_iteration = True

        if has_iteration is False:
            pytest.fail("No iteration")

    def test_dictone_on_some_column(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Cache.query("id", "method").limit(1)
        cache = query.one()
        assert query.dictone() == {
            "id": cache.id,
            "method": cache.method,
        }

    def test_dictone_on_some_column_with_label(self, rollback_registry):
        registry = rollback_registry
        Cache = registry.System.Cache
        query = Cache.query(
            Cache.id.label("n1"),
            Cache.method.label("t2"),
        ).limit(1)
        cache = query.one()
        assert query.dictone() == {
            "n1": cache.n1,
            "t2": cache.t2,
        }

    def test_dictfirst(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Cache.query()
        cache = query.first()
        assert query.dictfirst() == {
            "id": cache.id,
            "method": cache.method,
            "registry_name": cache.registry_name,
        }

    def test_dictfirst_on_some_column(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Cache.query("id", "method")
        cache = query.first()
        assert query.dictfirst() == {
            "id": cache.id,
            "method": cache.method,
        }

    def test_dictfirst_on_some_column_with_label(self, rollback_registry):
        registry = rollback_registry
        Cache = registry.System.Cache
        query = Cache.query(
            Cache.id.label("n1"),
            Cache.method.label("t2"),
        )
        cache = query.first()
        assert query.dictfirst() == {
            "n1": cache.n1,
            "t2": cache.t2,
        }

    def test_dictall(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Cache.query().limit(2)
        caches = query.all()

        def to_dict(cache):
            return {
                "id": cache.id,
                "method": cache.method,
                "registry_name": cache.registry_name,
            }

        dictall = query.dictall()
        for i in range(2):
            assert to_dict(caches[i]) in dictall

    def test_dictall_on_some_column(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Cache.query("id", "method").limit(2)
        caches = query.all()

        def to_dict(cache):
            return {
                "id": cache.id,
                "method": cache.method,
            }

        dictall = query.dictall()
        for i in range(2):
            assert to_dict(caches[i]) in dictall

    def test_dictall_on_some_column_with_label(self, rollback_registry):
        registry = rollback_registry
        Cache = registry.System.Cache
        query = Cache.query(
            Cache.id.label("n1"),
            Cache.method.label("t2"),
        ).limit(2)
        caches = query.all()

        def to_dict(cache):
            return {
                "n1": cache.n1,
                "t2": cache.t2,
            }

        dictall = query.dictall()
        for i in range(2):
            assert to_dict(caches[i]) in dictall

    def test_get_with_dict_use_prefix(self, rollback_registry):
        registry = rollback_registry
        entry = registry.System.Blok.query().get({"name": "anyblok-core"})
        assert entry is not None

    def test_get_with_kwargs(self, rollback_registry):
        registry = rollback_registry
        entry = registry.System.Blok.query().get(name="anyblok-core")
        assert entry is not None

    def test_str(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Sequence.query()
        assert str(query) == str(query.sql_statement)

    def test_repr(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Sequence.query()
        assert repr(query) == str(query.sql_statement)
