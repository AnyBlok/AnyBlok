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

anyblok._argsparse module
-------------------------

.. automodule:: anyblok._argsparse

.. autoclass:: ArgsParseManager
    :members:
    :noindex:

anyblok._imp module
-------------------

.. automodule:: anyblok._imp

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

.. warning:: TODO Class not finished yet

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

anyblok.databases module
------------------------

Management of the database

::

    adapter = getUtility(ISqlAlchemyDataBase, drivername)
    adapter.createdb(dbname)
    logger.info(adapter.listdb())
    adapter.dropdb(dbname)

anyblok.databases.postgres module
+++++++++++++++++++++++++++++++++

.. automodule:: anyblok.databases.postgres
.. autoclass:: ASqlAlchemyPostgres
    :members:
    :noindex:
