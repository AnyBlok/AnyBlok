.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

AnyBlok framework internals
===========================

anyblok module
--------------

.. automodule:: anyblok

.. autofunction:: start

.. autofunction:: load_init_function_from_entry_points

.. autofunction:: configuration_post_load

anyblok.declarations module
---------------------------

.. automodule:: anyblok.declarations

.. autoexception:: DeclarationsException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: Declarations
    :members:

anyblok.model module
--------------------

.. automodule:: anyblok.model

.. autoexception:: ModelException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoexception:: ViewException
    :members:
    :show-inheritance:
    :inherited-members:

anyblok.model.plugins module
----------------------------

.. automodule:: anyblok.model.plugins

.. autoclass:: ModelPluginBase
    :members:

Plugin: hybrid_method
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: anyblok.model.hybrid_method

.. autoclass:: HybridMethodPlugin
    :members:
    :show-inheritance:

Plugin: table_mapper
~~~~~~~~~~~~~~~~~~~~

.. automodule:: anyblok.model.table_and_mapper

.. autoclass:: TableMapperPlugin
    :members:
    :show-inheritance:

Plugin: event / SQLAlchemy event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: anyblok.model.event

.. autoclass:: EventPlugin
    :members:
    :show-inheritance:

.. autoclass:: SQLAlchemyEventPlugin
    :members:
    :show-inheritance:

Plugin: cache
~~~~~~~~~~~~~

.. automodule:: anyblok.model.cache

.. autoclass:: CachePlugin
    :members:
    :show-inheritance:

Plugin: field datetime
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: anyblok.model.field_datetime

.. autoclass:: AutoUpdatePlugin
    :members:
    :show-inheritance:


anyblok.mapper module
---------------------

.. automodule:: anyblok.mapper

.. autoexception:: ModelAttributeException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoexception:: ModelReprException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoexception:: ModelAttributeAdapterException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoexception:: MapperException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: ModelRepr
    :members:

.. autoclass:: ModelAttribute
    :members:

.. autoclass:: ModelMapper
    :members:

.. autoclass:: ModelAttributeMapper
    :members:

.. autofunction:: ModelAttributeAdapter

.. autofunction:: ModelAdapter

.. autofunction:: MapperAdapter

anyblok.config module
---------------------

.. automodule:: anyblok.config

.. autoexception:: ConfigurationException
    :members:
    :show-inheritance:
    :inherited-members:

.. autofunction:: get_db_name

.. autofunction:: get_url

.. autoclass:: Configuration
    :members:

anyblok.logging module
----------------------

.. automodule:: anyblok.logging

.. autoclass:: consoleFormatter
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: anyblokFormatter
    :members:
    :show-inheritance:
    :inherited-members:

.. autofunction:: log

anyblok.imp module
------------------

.. automodule:: anyblok.imp

.. autoexception:: ImportManagerException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: ImportManager
    :members:

anyblok.environment module
--------------------------

.. automodule:: anyblok.environment

.. autoexception:: EnvironmentException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: EnvironmentManager
    :members:

.. autoclass:: ThreadEnvironment
    :members:

anyblok.blok module
-------------------

.. automodule:: anyblok.blok

.. autoexception:: BlokManagerException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: BlokManager
    :members:

.. autoclass:: Blok
    :members:

anyblok.registry module
-----------------------

.. automodule:: anyblok.registry

.. autoexception:: RegistryManagerException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoexception:: RegistryException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: RegistryManager
    :members:

.. autoclass:: Registry
    :members:

anyblok.migration module
------------------------

.. automodule:: anyblok.migration

.. warning::
    AnyBlok use Alembic to do the dynamic migration, but Alembic does'nt detect
    all the change (primary key, ...), we must wait the Alembic or
    implement it in Alembic project before use it in AnyBlok

.. autoexception:: MigrationException
    :members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: MigrationReport
    :members:

.. autoclass:: MigrationConstraintForeignKey
    :members:

.. autoclass:: MigrationColumn
    :members:

.. autoclass:: MigrationConstraintCheck
    :members:

.. autoclass:: MigrationConstraintUnique
    :members:

.. autoclass:: MigrationConstraintPrimaryKey
    :members:

.. autoclass:: MigrationIndex
    :members:

.. autoclass:: MigrationTable
    :members:

.. autoclass:: Migration
    :members:

anyblok.field module
--------------------

.. automodule:: anyblok.field

.. autoclass:: Field
    :members:

.. autoclass:: Function
    :show-inheritance:
    :inherited-members:
    :members:

anyblok.column module
----------------------

.. automodule:: anyblok.column

.. autoclass:: Column
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Integer
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: BigInteger
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Boolean
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Float
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Decimal
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Date
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: DateTime
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Time
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Interval
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: String
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Text
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: StrSelection
    :members:

.. autoclass:: SelectionType
    :members:

.. autoclass:: Selection
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Json
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: LargeBinary
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Color
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Password
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: PhoneNumber
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Email
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Country
    :show-inheritance:
    :inherited-members:
    :members:

anyblok.relationship module
---------------------------

.. automodule:: anyblok.relationship

.. autoclass:: RelationShip
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Many2One
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: One2One
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: Many2Many
    :show-inheritance:
    :inherited-members:
    :members:

.. autoclass:: One2Many
    :show-inheritance:
    :inherited-members:
    :members:


anyblok._graphviz module
------------------------

.. automodule:: anyblok._graphviz

.. autoclass:: BaseSchema
    :members:

.. autoclass:: SQLSchema
    :members:

.. autoclass:: TableSchema
    :members:

.. autoclass:: ModelSchema
    :members:

.. autoclass:: ClassSchema
    :members:

anyblok.scripts module
----------------------

.. automodule:: anyblok.scripts

.. autofunction:: anyblok_createdb

.. autofunction:: anyblok_updatedb

.. autofunction:: anyblok_interpreter

.. autofunction:: anyblok_nose

.. autofunction:: anyblok2doc

anyblok.tests.testcase module
-----------------------------
.. automodule:: anyblok.tests.testcase

.. autoclass:: BlokTestCase
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: LogCapture
    :members:
    :undoc-members:
    :show-inheritance:
    :inherited-members:

.. autoclass:: DBTestCase
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: TestCase
    :members:
    :undoc-members:
    :show-inheritance:
