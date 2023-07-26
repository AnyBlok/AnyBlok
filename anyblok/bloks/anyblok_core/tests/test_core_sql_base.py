# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest


@pytest.mark.usefixtures("rollback_registry")
class TestCoreSqlBase:
    def test_insert(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        Blok.insert(name="OneBlok", state="undefined", version="0.0.0")
        blok = Blok.query().filter(Blok.name == "OneBlok").first()
        assert blok.state == "undefined"

    def test_multi_insert(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        Blok.multi_insert(
            dict(name="OneBlok", state="undefined", version="0.0.0"),
            dict(name="TwoBlok", state="undefined", version="0.0.0"),
            dict(name="ThreeBlok", state="undefined", version="0.0.0"),
        )
        states = (
            Blok.query("state")
            .filter(Blok.name.in_(["OneBlok", "TwoBlok", "ThreeBlok"]))
            .all()
        )
        states = [x[0] for x in states]
        assert states == ["undefined", "undefined", "undefined"]

    def test_from_primary_key(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        blok = Blok.query().first()
        blok2 = Blok.from_primary_keys(name=blok.name)
        assert blok == blok2

    def test_from_primary_keys(self, rollback_registry):
        registry = rollback_registry
        Cache = registry.System.Cache
        cache = Cache.query().first()
        cache2 = Cache.from_primary_keys(id=cache.id)
        assert cache == cache2

    def test_get_primary_key(self, rollback_registry):
        registry = rollback_registry
        assert registry.System.Blok.get_primary_keys() == ["name"]

    def test_get_primary_keys(self, rollback_registry):
        registry = rollback_registry
        pks = registry.System.Cache.get_primary_keys()
        assert "id" in pks

    def test_to_primary_key(self, rollback_registry):
        registry = rollback_registry
        blok = registry.System.Blok.query().first()
        assert blok.to_primary_keys() == dict(name=blok.name)

    def test_to_primary_keys(self, rollback_registry):
        registry = rollback_registry
        cache = registry.System.Cache.query().first()
        assert cache.to_primary_keys() == {
            "id": cache.id,
        }

    def test_fields_description(self, rollback_registry):
        registry = rollback_registry
        Cache = registry.System.Cache
        selections = [
            (k, v.__doc__ and v.__doc__.split("\n")[0] or k)
            for k, v in registry.loaded_namespaces.items()
        ]
        res = {
            "id": {
                "id": "id",
                "label": "Id",
                "model": None,
                "nullable": False,
                "primary_key": True,
                "type": "Integer",
            },
            "method": {
                "id": "method",
                "label": "Method",
                "model": None,
                "nullable": False,
                "primary_key": False,
                "type": "String",
            },
            "registry_name": {
                "id": "registry_name",
                "label": "Registry name",
                "model": None,
                "nullable": False,
                "primary_key": False,
                "type": "ModelSelection",
                "selections": selections,
            },
        }
        assert Cache.fields_description() == res

    def test_fields_description_limited_field(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        res = {
            "installed_version": {
                "id": "installed_version",
                "label": "Installed version",
                "model": None,
                "nullable": True,
                "primary_key": False,
                "type": "String",
            }
        }
        assert Blok.fields_description(fields=["installed_version"]) == res

    def test_fields_description_cache(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        res = {
            "short_description": {
                "id": "short_description",
                "label": "Short description",
                "model": None,
                "nullable": True,
                "primary_key": False,
                "type": "Function",
            }
        }
        assert Blok.fields_description(fields=["short_description"]) == res
        Blok.loaded_fields["short_description"] = "Test"
        assert Blok.fields_description(fields=["short_description"]) == res
        Blok.clear_all_model_caches()
        assert Blok.fields_description(fields=["short_description"]) != res

    def test_to_dict(self, rollback_registry):
        registry = rollback_registry
        Cache = registry.System.Cache
        cache = Cache.query().first()
        assert cache.to_dict() == {
            "id": cache.id,
            "method": cache.method,
            "registry_name": cache.registry_name,
        }

    def test_to_dict_on_some_columns(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        blok = Blok.query().first()
        assert blok.to_dict(
            "name", "installed_version", "short_description"
        ) == {
            "name": blok.name,
            "installed_version": blok.installed_version,
            "short_description": blok.short_description,
        }

    def test_select_sql_statement_with_column(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        assert Blok.execute_sql_statement(
            Blok.select_sql_statement("name")
            .where(Blok.name == "anyblok-core")
            .limit(1)
        ).one() == ("anyblok-core",)

    def test_from_multi_primary_keys(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        blok_names = Blok.from_multi_primary_keys(
            dict(name="anyblok-core"),
            dict(name="anyblok-test"),
        ).name
        assert "anyblok-core" in blok_names
        assert "anyblok-test" in blok_names

    def test_from_multi_primary_keys_empty(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        assert Blok.from_multi_primary_keys() == []

    def test_get_hybrid_property_columns(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        columns = Blok.get_hybrid_property_columns()
        for x in [
            "name",
            "state",
            "author",
            "order",
            "version",
            "installed_version",
        ]:
            assert x in columns
