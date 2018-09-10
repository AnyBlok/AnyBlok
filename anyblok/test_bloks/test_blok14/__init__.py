# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok


class TestBlok(Blok):

    version = '1.0.0'
    table_exist_before_automigration = None
    table_exist_after_automigration = None

    @classmethod
    def import_declaration_module(cls):
        from . import test  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import test
        reload(test)

    def is_table_exist(self):
        return bool(self.registry.execute("""
            select count(*)
            from pg_catalog.pg_tables
            where tablename = 'test';
        """).fetchone()[0])

    def pre_migration(self, latest_version):
        self.__class__.table_exist_before_automigration = self.is_table_exist()

    def post_migration(self, latest_version):
        self.__class__.table_exist_after_automigration = self.is_table_exist()
