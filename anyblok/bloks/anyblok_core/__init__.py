# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok
from anyblok.release import version
from logging import getLogger
logger = getLogger(__name__)


class AnyBlokCore(Blok):
    """This Blok is required in all AnyBlok applications.

    This Blok provides the main fonctionalities for Bloks management (install,
    update, uninstall…).

    It also brings the representation of Anyblok objects (Models, Fields, etc.)
    within the database itself, and some fundamental facilities.

    * Core Models

      These are pure code Models, used as base classes:

      - Base: inherited by all Models
      - SqlBase: inherited by all models backed by an SQL table
      - SqlViewBase: inherited by all models bacled by an SQL view

    * System Models

      These correspond to actual tables in the table. They provide reflection
      or fundamental facilities.

      - Blok: represent all *available* Bloks, with their state and more
      - Model
      - Field
      - Column
      - Relationship
      - :class:`Sequence <.system.sequence.Sequence>`: database sequences,
        for use in applications.
      - :class:`Parameter <.system.parameter.Parameter>`: application
        parameters
    """

    version = version
    autoinstall = True
    priority = 0
    author = 'Suzanne Jean-Sébastien'
    logo = '../anyblok-logo_alpha_256.png'

    def pre_migration(self, latest_version):  # pragma: no cover
        if latest_version is None:
            return

        if latest_version < '0.4.1':
            self.pre_migration_0_4_1_fields_become_polymorphic(latest_version)

    def pre_migration_0_4_1_fields_become_polymorphic(
        self, latest_version
    ):  # pragma: no cover
        logger.info("Pre Migration %s => %s: Field, Column, Relation Ship "
                    "become prolymophic models" % (latest_version,
                                                   self.version))
        system_field = self.anyblok.migration.table('system_field')
        system_field.column().add(self.anyblok.System.Field.entity_type)
        self.anyblok.execute(
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
        self.anyblok.execute(
            query % {'entity_type': 'Model.System.Column',
                     'table': 'system_column'})
        self.anyblok.execute(
            query % {'entity_type': 'Model.System.RelationShip',
                     'table': 'system_relationship'})
        system_column = self.anyblok.migration.table('system_column')
        system_column.column('code').drop()
        system_column.column('ftype').drop()
        system_column.column('label').drop()
        system_relationship = self.anyblok.migration.table(
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
