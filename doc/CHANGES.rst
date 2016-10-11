.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

CHANGELOG
=========

0.9.2 (2016-10-12)
------------------

* [FIX] setup.py: error with pip

0.9.1 (2016-10-3)
-----------------

* [FIX] migration testcase
* [FIX] graphviz FORMATS
* [FIX] travis configuration

0.9.0 (2016-07-11)
------------------

* [REF] add Configuration.has method
* [FIX] test migration, force to load registry with unittest=True
* [FIX] test event
* [FIX] test blok
* [FIX] mapper with None parameter
* [FIX] add set_defaults in parser to update configuration dict
* [FIX] one2many remote columns
* [FIX] load anyblok.init in the unit test
* [IMP] Add plugins by configuration for:

  * Registry
  * Migration
  * get_url

* [IMP] add LogCapture
* [IMP] TestCase.Configuration, use to update Configuration only in 
  a context manager
* [IMP] add Registry.db_exists class method, check with the configuration
  and the db_name if the connection is possible

0.8.5 (2016-06-20)
------------------

* [FIX] utf-8 encoding
* [REF] move bitbucket (mergurial) to github (git)

0.8.4 (2016-06-14)
------------------

* [FIX] io/xml/importer one2many field
* [FIX] install blok, who are not in the blok list yet. But the blok is loaded

0.8.3 (2016-04-18)
------------------

* [FIX] cache and classmethod_cache on SQL model
* [ADD] is_installed classmethod cache

0.8.2 (2016-04-06)
------------------

* [REF] IO.Mapping methods delete and multi_delete can remove entry
* [FIX] datetime with timezone use timezone.localize, better than
  datetime.replace(tzinfo=...)
* [ADD] update sphinx extension

0.8.1 (2016-03-15)
------------------

* [FIX] `#21 <https://bitbucket.org/jssuzanne/anyblok/issues/21/update-setter-for-decimal>`_
  Improve Decimal column setter
* [FIX] `#22 <https://bitbucket.org/jssuzanne/anyblok/issues/22/string-ustring-text-utext-columns-save>`_
  String, uString, Text and uText write '' in database for False value
* [FIX] Change the external_id save in a two way
* [FIX] `#23 <https://bitbucket.org/jssuzanne/anyblok/issues/23/selection-field-when-nullable-true-doesnt>`_
  Column.Selection with None value, don't return 'None' value by the getter

0.8.0 (2016-02-05)
------------------

.. warning::

    Break the compatibility with the previous version of anyblok

    * update method on the model
      replace ::

          obj.update({field1: val1, ...})

      by::

          obj.update(field1=val1, ...)

* [REF] session expire is now on the attribute, the update method is refactored
  too.
* [FIX] blok: update version if the version change
* [REF] add required blok, this bloks is installed and updated by the scripts
  anyblok_updatedb and anyblok_createdb
* [ADD] Add Color Column
* [REF] column can be encrypted
* [REF] DataTime column is not a naive datatime value
* [ADD] Add Password Column
* [ADD] Add UUID Column
* [ADD] Add URL Column

0.7.2 (2016-01-14)
------------------

* [FIX] delete flush after remove of the session
* [FIX] nose plugins
* [FIX] does'nt destroy automaticly constraints (not created by anyblok),
  indexes (not created by anyblok), columns, tables by automigration, add
  options to force the delete of its.
* [REF] standardize the constraint and index names
* [FIX] Multi declaration of the same foreign key in the case of M2O and O2O
* [REF] SqlBase.update, become hight level meth

0.7.1 (2016-01-08)
------------------

* [FIX] didn't cast the config data from the config file
* [IMP] copy init entry point from anyblok_pyramid

0.7.0 (2016-01-07)
------------------

.. warning::

    Python 3.2 is not supported

* [REF] Add options to give database url, No break compatibility
* [REF] the argument of ArgumentParser can be add in the configuration
    - Improve the help of the application
    - Improve the type of the configuration, Work also with config file.
    - Adapt current configuration
* [REF] start to use sqlalchemy-utils, replace the database management
* [IMP] `#18 <https://bitbucket.org/jssuzanne/anyblok/issues/18/forbidden-the-declaration-of-sqlachemy>`_
  Forbidden the declaration of SQLAchemy column or relationship
* [REF] `#15 <https://bitbucket.org/jssuzanne/anyblok/issues/15/speed-up-the-unittest>`_
  Refactor unittest case to not create/drop database for each test
* [FIX] `#19 <https://bitbucket.org/jssuzanne/anyblok/issues/19/migration-contrainte>`_
  During migration if an unique constraint must be apply without unique
  value, then the constraint will be ignore and log a warning. No break the
  instalation of the blok
* [FIX] `#20 <https://bitbucket.org/jssuzanne/anyblok/issues/20/update-meth-must-refresh-the-instance-when>`_
  Update meth: expire the instance cause of relationship
* [IMP] refresh and expire meth on model
* [REF] delete obj, flush the session and delete the instance of obj of the
  session, before expire all the session, the goal is to reload the
  relation ship.
* [REF] `#13 <https://bitbucket.org/jssuzanne/anyblok/issues/13/refactor-inheritance-tree>`_
  Remove association model, replace it by call at the Blok definition
* [IMP] `#14 <https://bitbucket.org/jssuzanne/anyblok/issues/14/add-conflicting-link-between-bloks>`_
  Add conflicting link between blok, two blok who are in conflict can be installed
  if the other is installed

0.6.0 (2016-01-07)
------------------

* [REF] unittest isolation
* [IMP] possibility to apply an extension for sqlalchemy
* [ADD] pool configuration

0.5.2 (2015-09-28)
------------------

* [IMP] extension for Sphinx and autodoc
* [ADD] API doc in doc
* [ADD] add foreign key option in relation ship
* [CRITICAL FIX] the EnvironnementManager didn't return the good scoped method
  for SQLAlchemy
* [CRITICAL FIX] the precommit_hook was not isolated by session
* [REF] add a named argument ``must_be_loaded_by_unittest``, by dafault False,
  in ``Configuration.add`` to indicate if the function must be call during the
  initialisation of the unittest, generally for the configuration initialized
  by Environ variable

0.5.1 (2015-08-29)
------------------

* [IMP] unload declaration type callback

0.5.0 (2015-08-28)
------------------

.. warning::

    Break the compatibility with the previous version of anyblok

    * cache, classmethod_cache, hybrid_method and listen
      replace::

        from anyblok import Declarations
        cache = Declarations.cache
        classmethod_cache = Declarations.classmethod_cache
        hybrid_method = Declarations.hybrid_method
        addListener = Declarations.addListener

      by::

        from anyblok.declarations import (cache, classmethod_cache,
                                          hybrid_method, listen)

      .. note::

        The listener can declare SQLAlchemy event

    * declaration of the foreign key
      replace::

        @register(Model):
        class MyClass:

            myfield = Integer(foreign_key=(Model.System.Blok, 'name'))
            myotherfield = Integer(foreign_key=('Model.System.Blok', 'name'))

      by::

        @register(Model):
        class MyClass:

            myfield = Integer(foreign_key=Model.System.Blok.use('name'))
            myotherfield = Integer(foreign_key="Model.System.Blok=>name")

* [IMP] add ``pop`` behaviour on **Model.System.Parameter**
* [REF] Load configuration befoare load bloks, to use Configuration during
  the declaration
* [FIX] all must return InstrumentedList, also when the result is empty
* [FIX] to_dict must not cast column
* [REF] add third entry in foreign key declaration to add options
* [IMP] ModelAttribute used to declarate the need of specific attribute and
  get the attribute or the foreign key from this attribute
* [IMP] ModelAttributeAdapter, get a ModelAttribute from ModelAttribute or str
* [IMP] ModelRepr, Speudo representation of a Model
* [IMP] ModelAdapter, get a ModelRepr from ModelRepr or str
* [IMP] ModelMapper and ModelAttributeMapper
* [REF] Event, the declaration of an event can be an anyblok or a sqlalchemy event
* [REF] the foreign key must be declared with ModelAttribute
* [REF] Use Adapter for Model and attribute in relation ship
* [REF] hybrid_method, cache and classmethod_cache are now only impotable decorator function
* [IMP] in column the default can be a classmethod name
* [REF] replace all the field (prefix, suffic, ...) by a formater field.
  It is a python formater string
* [IMP] Sequence column
* [IMP] add the default system or user configuration file

0.4.1 (2015-07-22)
------------------

.. warning::

    Field Function change, fexp is required if you need filter

* [FIX] Field.Function, fexp is now a class method
* [REF] reduce flake8 complexity
* [REF] refactor field function
* [FIX] inherit relation ship from another model, thank Simon ANDRÉ for the
  bug report
* [REF] table/mapper args definition
* [REF] Refactor Field, Column, RelationShip use now polymophic inherit
* [FIX] Foreign key constraint, allow to add and drop constraint on more than
  one foreign key
* [ADD] update-all-bloks option
* [ADD] pre / post migration
* [REF] UML Diagram is now with autodoc script
* [REF] SQL Diagram is now with autodoc script
* [REF] Add **extend** key word in configuration file to extend an existing
  configuration

0.4.0 (2015-06-21)
------------------

.. warning::

    Break the compatibility with the previous version of anyblok

* [REF] Add the possibility to add a logging file by argparse
* [ADD] No auto migration option
* [ADD] Plugin for nose to run unit test of the installed bloks
* [REF] The relation ship can be reference more than one foreign key
* [IMP] Add define_table/mapper_args methods to fill __table/mapper\_args\_\_
  class attribute need to configure SQLAlachemy models
* [REF] Limit the commit in the registry only when the SQLA Session factory
  is recreated
* [REF] Commit and re-create the SQLA Session Factory, at installation, only
  if the number of Session inheritance of the number of Query inheritance
  change, else keep the same session
* [REF] Exception is not a Declarations type
* [FIX] Reload fonctionnality in python 3.2
* [REF] Remove the Declarations typs Field, Column, RelationShip, they are
  replaced by python import
* [REF] rename **ArgsParseManager** by **Configuration**
* [REF] rename **reload_module_if_blok_is_reloaded** by
  **reload_module_if_blok_is_reloading** method on blok
* [REF] rename **import_cfg_file** by **import_file** method on blok
* [REF] Consistency the argsparse configuration
* [REF] refactor part_to_load, the entry points loaded is bloks
* [IMP] Allow to define another column name in the table versus model
* [FIX] add importer for import configuration file
* [FIX] x2M importer without field just, external id

0.3.5 (2015-05-10)
------------------

* [IMP] When a new column is add, if the column have a default value, then
  this value will be added in all the entries where the value is null for this
  column
* [REF] import_cfg_file remove the importer when import has done

0.3.4 (2015-05-10)
------------------

* [ADD] logger.info on migration script to indicate what is changed
* [IMP] Add sequence facility in the declaration of Column
* [ADD] ADD XML Importer

0.3.3 (2015-05-04)
------------------

* [FIX] createdb script

0.3.2 (2015-05-04)
------------------

* [IMP] doc
* [REF] Use logging.config.configFile

0.3.1 (2015-05-04)
------------------

* [IMP] Update setup to add documentation files and blok's README

0.3.0 (2015-05-03)
------------------

* [IMP] Update Doc
* [FIX] Remove nullable column, the nullable constraint is removed not the column
* [ADD] Formater, convert value 2 str or str 2 value, with or without mapping
* [ADD] CSV Importer
* [REF] CSV Exporter to use Formater

0.2.12 (2015-04-29)
-------------------

* [IMP] CSV Exporter
* [IMP] Exporter Model give external ID behaviour
* [ADD] Sequence model (Model.System.Sequence)
* [ADD] fields_description cached_classmethod with invalidation
* [ADD] Parameter Model (Model.System.Parameter)
* [FIX] environnement variable for test unitaire

0.2.11 (2015-04-26)
-------------------

* [FIX] UNIT test createdb with prefix

0.2.10 (2015-04-26)
-------------------

* [IMP] add enviroment variable for database information
* [ADD] argsparse option install all bloks
* [FIX] Python 3.2 need that bloks directory are python modules, add empty __init__ file

0.2.9 (2015-04-18)
------------------

* [FIX] Add all rst at the main path of all the bloks

0.2.8 (2015-04-16)
------------------

* [IMP] unittest on SQLBase
* [IMP] add delete method on SQLBase to delete une entry from an instance of the model
* [REF] rename get_primary_keys to get_mapping_primary_keys, cause of get_primary_keys
  already exist in SQLBase

0.2.7 (2015-04-15)
------------------

* [IMP] Add IPython support for interpreter
* [REF] Update and Standardize the method to field the models (Field, Column, RelationShip)
  now all the type of the column go on the ftype and comme from the name of the class

0.2.6 (2015-04-11)
------------------

* [FIX] use the backref name to get the label of the remote relation ship
* [FIX] add type information of the simple field

0.2.5 (2015-03-23)
------------------

* [FIX] In the parent / children relationship, where the pk is on a mixin or
  from inherit
* [FIX] How to Environment
* [FIX] Many2Many declared in Mixin
* [IMP] Many2One can now declared than the local column must be unique (
  only if the local column is not declared in the model)

0.2.3 (2015-03-23)
------------------

.. warning::

    This version can be not compatible with the version **0.2.2**. Because
    in the foregn key model is a string you must replace the tablename by
    the registry name

* [FIX] Allow to add a relationship on the same model, the main use is to add
  parent / children relation ship on a model, They are any difference with
  the declaration of ta relation ship on another model
* [REF] standardize foreign_key and relation ship, if the str which replace
  the Model Declarations is now the registry name

0.2.2 (2015-03-15)
------------------

* [REF] Unittest
    * TestCase and DBTestCase are only used for framework
    * BlokTestCase is used:
        - by ``run_exit`` function to test all the installed bloks
        - at the installation of a blok if wanted

0.2.0 (2015-02-13)
------------------

.. warning::

    This version is not compatible with the version **0.1.3**

* [REF] Import and reload are more explicite
* [ADD] IO:
    * Mapping: Link between Model instance and (Model, str key)

* [ADD] Env in registry_base to access at EnvironmentManager without to import
  it at each time
* [IMP] doc add how to on the environment

0.1.3 (2015-02-03)
------------------

* [FIX] setup long description, good for pypi but not for easy_install

0.1.2 (2015-02-02)
------------------

* [REFACTOR] Allow to declare Core components
* [ADD] Howto declare Core / Type
* [FIX] Model can only inherit simple python class, Mixin or Model
* [FIX] Mixin inherit chained
* [FIX] Flake8

0.1.1 (2015-01-23)
------------------

* [FIX] version, documentation, setup

0.1.0 (2015-01-23)
------------------

Main version of AnyBlok. You can with this version

* Create your own application
* Connect to a database
* Define bloks
* Install, Update, Uninstall the blok
* Define field types
* Define Column types
* Define Relationship types
* Define Core
* Define Mixin
* Define Model (SQL or not)
* Define SQL view
* Define more than one Model on a specific table
* Write unittest for your blok
