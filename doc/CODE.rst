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

.. autoexception:: DeclarationsException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoclass:: Declarations
    :members:
    :noindex:

anyblok.model module
--------------------

.. automodule:: anyblok.model

.. autoexception:: ModelException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoexception:: ViewException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

anyblok.mapper module
---------------------

.. automodule:: anyblok.mapper

.. autoexception:: ModelAttributeException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoexception:: ModelReprException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoexception:: ModelAttributeAdapterException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoexception:: MapperException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoclass:: ModelRepr
    :members:
    :noindex:

.. autoclass:: ModelAttribute
    :members:
    :noindex:

.. autoclass:: ModelMapper
    :members:
    :noindex:

.. autoclass:: ModelAttributeMapper
    :members:
    :noindex:

.. autofunction:: ModelAttributeAdapter
    :noindex:

.. autofunction:: ModelAdapter
    :noindex:

.. autofunction:: MapperAdapter
    :noindex:

anyblok.config module
---------------------

.. automodule:: anyblok.config

.. autoexception:: ConfigurationException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoclass:: Configuration
    :members:
    :noindex:

anyblok.logging module
----------------------

.. automodule:: anyblok.logging

.. autoclass:: consoleFormatter
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoclass:: anyblokFormatter
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autofunction:: log
    :noindex:

anyblok.imp module
------------------

.. automodule:: anyblok.imp

.. autoexception:: ImportManagerException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoclass:: ImportManager
    :members:
    :noindex:

anyblok.environment module
--------------------------

.. automodule:: anyblok.environment

.. autoexception:: EnvironmentException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoclass:: EnvironmentManager
    :members:
    :noindex:

.. autoclass:: ThreadEnvironment
    :members:
    :noindex:

anyblok.blok module
-------------------

.. automodule:: anyblok.blok

.. autoexception:: BlokManagerException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoclass:: BlokManager
    :members:
    :noindex:

.. autoclass:: Blok
    :members:
    :noindex:

anyblok.registry module
-----------------------

.. automodule:: anyblok.registry

.. autoexception:: RegistryManagerException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

.. autoexception:: RegistryException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

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
    all the change (primary key, ...), we must wait the Alembic or
    implement it in Alembic project before use it in AnyBlok

.. autoexception:: MigrationException
    :members:
    :noindex:
    :show-inheritance:
    :inherited-members:

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
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

anyblok.column module
----------------------

.. automodule:: anyblok.column

.. autoclass:: Column
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Integer
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: SmallInteger
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: BigInteger
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Boolean
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Float
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Decimal
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Date
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: DateTime
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Time
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Interval
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: String
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: uString
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Text
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: uText
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: StrSelection
    :members:
    :noindex:

.. autoclass:: SelectionType
    :members:
    :noindex:

.. autoclass:: Selection
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: JsonType
    :members:
    :noindex:

.. autoclass:: Json
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: LargeBinary
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Color
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Password
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

anyblok.relationship module
---------------------------

.. automodule:: anyblok.relationship

.. autoclass:: RelationShip
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Many2One
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: One2One
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: Many2Many
    :show-inheritance:
    :inherited-members:
    :members:
    :noindex:

.. autoclass:: One2Many
    :show-inheritance:
    :inherited-members:
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

anyblok.scripts module
----------------------

.. automodule:: anyblok.scripts

.. autofunction:: createdb
    :noindex:

.. autofunction:: updatedb
    :noindex:

.. autofunction:: interpreter
    :noindex:

.. autofunction:: run_exit
    :noindex:

.. autofunction:: cron_worker
    :noindex:

.. autofunction:: registry2doc
    :noindex:
