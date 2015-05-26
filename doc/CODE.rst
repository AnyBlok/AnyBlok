.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

AnyBlok framework
=================

anyblok module
--------------

.. automodule:: anyblok

.. autofunction:: start
    :noindex:

anyblok.declarations module
---------------------------

.. automodule:: anyblok.declarations

.. autoclass:: Declarations
    :members:
    :noindex:

anyblok.config module
---------------------

.. automodule:: anyblok.config

.. autoclass:: Configuration
    :members:
    :noindex:

anyblok.imp module
------------------

.. automodule:: anyblok.imp

.. autoclass:: ImportManager
    :members:
    :noindex:

anyblok.environment module
--------------------------

.. automodule:: anyblok.environment

.. autoclass:: EnvironmentManager
    :members:
    :noindex:

.. autoclass:: ThreadEnvironment
    :members:
    :noindex:

anyblok.blok module
-------------------

.. automodule:: anyblok.blok

.. autoclass:: BlokManager
    :members:
    :noindex:

.. autoclass:: Blok
    :members:
    :noindex:

anyblok.registry module
-----------------------

.. automodule:: anyblok.registry

.. autoclass:: RegistryManager
    :members:
    :noindex:

.. autoclass:: Registry
    :members:
    :noindex:

anyblok.migration module
------------------------

.. automodule:: anyblok.migration

.. warning::
    AnyBlok use Alembic to do the dynamic migration, but Alembic does'nt detect
    all the change (Foreifn key, primary key), we must wait the Alembic or
    implement it in Alembic project before use it in AnyBlok

.. autoclass:: MigrationReport
    :members:
    :noindex:

.. autoclass:: MigrationConstraintForeignKey
    :members:
    :noindex:

.. autoclass:: MigrationColumn
    :members:
    :noindex:

.. autoclass:: MigrationConstraintCheck
    :members:
    :noindex:

.. autoclass:: MigrationConstraintUnique
    :members:
    :noindex:

.. autoclass:: MigrationConstraintPrimaryKey
    :members:
    :noindex:

.. autoclass:: MigrationIndex
    :members:
    :noindex:

.. autoclass:: MigrationTable
    :members:
    :noindex:

.. autoclass:: Migration
    :members:
    :noindex:

anyblok.field module
--------------------

.. automodule:: anyblok.field

.. autoclass:: Field
    :members:
    :noindex:

.. autoclass:: Function
    :members:
    :noindex:

anyblok.column module
----------------------

.. automodule:: anyblok.column

.. autoclass:: Column
    :members:
    :noindex:

.. autoclass:: Integer
    :members:
    :noindex:

.. autoclass:: SmallInteger
    :members:
    :noindex:

.. autoclass:: BigInteger
    :members:
    :noindex:

.. autoclass:: Boolean
    :members:
    :noindex:

.. autoclass:: Float
    :members:
    :noindex:

.. autoclass:: Decimal
    :members:
    :noindex:

.. autoclass:: Date
    :members:
    :noindex:

.. autoclass:: DateTime
    :members:
    :noindex:

.. autoclass:: Time
    :members:
    :noindex:

.. autoclass:: Interval
    :members:
    :noindex:

.. autoclass:: String
    :members:
    :noindex:

.. autoclass:: uString
    :members:
    :noindex:

.. autoclass:: Text
    :members:
    :noindex:

.. autoclass:: uText
    :members:
    :noindex:

.. autoclass:: StrSelection
    :members:
    :noindex:

.. autoclass:: SelectionType
    :members:
    :noindex:

.. autoclass:: Selection
    :members:
    :noindex:

.. autoclass:: JsonType
    :members:
    :noindex:

.. autoclass:: Json
    :members:
    :noindex:

.. autoclass:: LargeBinary
    :members:
    :noindex:


anyblok._graphviz module
------------------------

.. automodule:: anyblok._graphviz

.. autoclass:: BaseSchema
    :members:
    :noindex:

.. autoclass:: SQLSchema
    :members:
    :noindex:

.. autoclass:: TableSchema
    :members:
    :noindex:

.. autoclass:: ModelSchema
    :members:
    :noindex:

.. autoclass:: ClassSchema
    :members:
    :noindex:

anyblok.databases module
------------------------

Management of the database

::

    bdd = anyblok.BDD[db_driver_name]
    bdd.createdb(db_name)
    logger.info(bdd.listdb())
    bdd.dropdb()

anyblok.databases.postgres module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: anyblok.databases.postgres
.. autoclass:: SqlAlchemyPostgres
    :members:
    :noindex:

anyblok.scripts module
----------------------

.. automodule:: anyblok.scripts

.. autofunction:: createdb
    :noindex:

.. autofunction:: updatedb
    :noindex:

.. autofunction:: interpreter
    :noindex:

.. autofunction:: sqlschema
    :noindex:

.. autofunction:: modelschema
    :noindex:
