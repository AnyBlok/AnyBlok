# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok
from anyblok.release import version
from logging import getLogger
logger = getLogger(__name__)


class AnyBlokCore(Blok):
    """
    This blok is required by all anyblok application. This blok define the main
    fonctionnality to install, update and uninstall blok. And also list the
    known models, fields, columns and relationships
    """

    version = version
    autoinstall = True
    priority = 0

    def pre_migration(self, latest_version):
        if latest_version is not None and latest_version < '0.4.1':
            self.pre_migration_0_4_1_fields_become_polymorphic(latest_version)

    def pre_migration_0_4_1_fields_become_polymorphic(self, latest_version):
        logger.info("Pre Migration %s => %s: Field, Column, Relation Ship "
                    "become prolymophic models" % (latest_version,
                                                   self.version))
        system_field = self.registry.migration.table('system_field')
        system_field.column().add(self.registry.System.Field.entity_type)
        self.registry.execute(
            "UPDATE system_field SET entity_type='Model.System.Field'")
        query = """
            INSERT INTO system_field (
                name,
                model,
                code,
                label,
                ftype,
                entity_type)
            SELECT
                name,
                model,
                code,
                label,
                ftype,
                '%(entity_type)s' AS entity_type
            FROM %(table)s
        """
        self.registry.execute(
            query % {'entity_type': 'Model.System.Column',
                     'table': 'system_column'})
        self.registry.execute(
            query % {'entity_type': 'Model.System.RelationShip',
                     'table': 'system_relationship'})
        system_column = self.registry.migration.table('system_column')
        system_column.column('code').drop()
        system_column.column('ftype').drop()
        system_column.column('label').drop()
        system_relationship = self.registry.migration.table(
            'system_relationship')
        system_relationship.column('code').drop()
        system_relationship.column('ftype').drop()
        system_relationship.column('label').drop()

    @classmethod
    def import_declaration_module(cls):
        from . import core  # noqa
        from . import system  # noqa
        from . import authorization  # noqa
        from . import documentation  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import core
        reload(core)
        from . import system
        reload(system)
        from . import authorization
        reload(authorization)
        from . import documentation
        reload(documentation)
