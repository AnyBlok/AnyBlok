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
