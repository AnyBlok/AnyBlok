.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

CHANGELOG
=========

Future
------

0.3.1
-----

* [IMP] Update setup to add documentation files and blok's README

0.3.0
-----

* [IMP] Update Doc
* [FIX] Remove nullable column, the nullable constraint is removed not the column
* [ADD] Formater, convert value 2 str or str 2 value, with or without mapping
* [ADD] CSV Importer
* [REF] CSV Exporter to use Formater

0.2.12
------

* [IMP] CSV Exporter
* [IMP] Exporter Model give external ID behaviour
* [ADD] Sequence model (Model.System.Sequence)
* [ADD] fields_description cached_classmethod with invalidation
* [ADD] Parameter Model (Model.System.Parameter) 
* [FIX] environnement variable for test unitaire

0.2.11
------

* [FIX] UNIT test createdb with prefix

0.2.10
------

* [IMP] add enviroment variable for database information
* [ADD] argsparse option install all bloks
* [FIX] Python 3.2 need that bloks directory are python modules, add empty __init__ file

0.2.9
-----

* [FIX] Add all rst at the main path of all the bloks

0.2.8
-----

* [IMP] unittest on SQLBase
* [IMP] add delete method on SQLBase to delete une entry from an instance of the model
* [REF] rename get_primary_keys to get_mapping_primary_keys, cause of get_primary_keys
  already exist in SQLBase

0.2.7
-----

* [IMP] Add IPython support for interpreter
* [REF] Update and Standardize the method to field the models (Field, Column, RelationShip)
  now all the type of the column go on the ftype and comme from the name of the class

0.2.6
-----

* [FIX] use the backref name to get the label of the remote relation ship
* [FIX] add type information of the simple field

0.2.5
-----

* [FIX] In the parent / children relationship, where the pk is on a mixin or
  from inherit
* [FIX] How to Environment
* [FIX] Many2Many declared in Mixin
* [IMP] Many2One can now declared than the local column must be unique (
  only if the local column is not declared in the model)

0.2.3
-----

.. warning::

    This version can be not compatible with the version **0.2.2**. Because
    in the foregn key model is a string you must replace the tablename by
    the registry name

* [FIX] Allow to add a relationship on the same model, the main use is to add
  parent / children relation ship on a model, They are any difference with
  the declaration of ta relation ship on another model
* [REF] standardize foreign_key and relation ship, if the str which replace
  the Model Declarations is now the registry name

0.2.2
-----

* [REF] Unittest
    * TestCase and DBTestCase are only used for framework
    * BlokTestCase is used:
        - by ``run_exit`` function to test all the installed bloks
        - at the installation of a blok if wanted

0.2.0
-----

.. warning::

    This version is not compatible with the version **0.1.3**

* [REF] Import and reload are more explicite
* [ADD] IO:
    * Mapping: Link between Model instance and (Model, str key)

* [ADD] Env in registry_base to access at EnvironmentManager without to import
  it at each time
* [IMP] doc add how to on the environment

0.1.3
-----

* [FIX] setup long description, good for pypi but not for easy_install

0.1.2
-----

* [REFACTOR] Allow to declare Core components
* [ADD] Howto declare Core / Type
* [FIX] Model can only inherit simple python class, Mixin or Model
* [FIX] Mixin inherit chained
* [FIX] Flake8

0.1.1
-----

* [FIX] version, documentation, setup

0.1.0
-----

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
