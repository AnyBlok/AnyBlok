AnyBlok framework
=================

anyblok module
--------------

.. automodule:: anyblok
.. autoclass:: AnyBlok
    :members:
    :undoc-members:
    :noindex:

anyblok._argsparse module
-------------------------

.. automodule:: anyblok._argsparse

.. autoexception:: ArgsParseManagerException
    :show-inheritance:
    :noindex:

.. autoclass:: ArgsParseManager
    :members:
    :noindex:

anyblok._imp module
-------------------

.. automodule:: anyblok._imp

.. autoexception:: ImportManagerException
    :show-inheritance:
    :noindex:

.. autoclass:: ImportManager
    :members:
    :noindex:

anyblok._logging module
-----------------------

.. automodule:: anyblok._logging
    :show-inheritance:
    :members:
    :noindex:


anyblok.environment module
--------------------------

.. automodule:: anyblok.environment

.. autoexception:: EnvironmentException
    :show-inheritance:
    :noindex:

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
    :show-inheritance:
    :members:
    :noindex:

.. autoclass:: BlokManager
    :members:
    :noindex:

.. autoclass:: Blok
    :members:
    :noindex:

anyblok.registry module
-----------------------

.. automodule:: anyblok.registry

.. warning:: TODO Class not finished yet

.. autoexception:: RegistryManagerException
    :show-inheritance:
    :members:
    :noindex:

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

.. autoexception:: MigrationException
    :show-inheritance:
    :members:
    :noindex:

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

anyblok.interface module
------------------------

.. automodule:: anyblok.interface

.. autoexception:: CoreInterfaceException
    :show-inheritance:
    :members:
    :noindex:

.. autoclass:: ACoreInterface
    :members:
    :noindex:

anyblok.databases module
------------------------

Management of the database

anyblok.databases.postgres module
+++++++++++++++++++++++++++++++++

.. automodule:: anyblok.databases.postgres
.. autoclass:: ASqlAlchemyPostgres
    :members:
    :noindex:

anyblok.core module
-------------------

.. automodule:: anyblok.core
.. autoclass:: ACore
    :members: target_registry, remove_registry
    :noindex:

anyblok.field module
--------------------

.. automodule:: anyblok.field

.. autoexception:: FieldException
    :members:
    :show-inheritance:
    :noindex:

.. autoclass:: AField
    :members: target_registry, remove_registry
    :noindex:

anyblok.column module
---------------------

.. automodule:: anyblok.column

.. autoclass:: AColumn
    :members: target_registry, remove_registry
    :show-inheritance:
    :noindex:

anyblok.relationship module
---------------------------

.. automodule:: anyblok.relationship

.. autoclass:: ARelationShip
    :members: target_registry, remove_registry
    :show-inheritance:
    :noindex:

anyblok.mixin module
--------------------

.. automodule:: anyblok.mixin

.. autoclass:: AMixin
    :members: target_registry, remove_registry
    :noindex:

anyblok.model module
--------------------

.. automodule:: anyblok.model

.. autoclass:: AModel
    :members: target_registry, remove_registry
    :noindex:
