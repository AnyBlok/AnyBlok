.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

ROADMAP
=======

Next step for the 0.2
---------------------

* Access Rules / Roles
* Add logo and slogan
* Update doc

To implement
------------

* Add RelationShip model in anyblok-core and refactor the get column http://docs.sqlalchemy.org/en/latest/faq.html#how-do-i-get-a-list-of-all-columns-relationships-mapped-attributes-etc-given-a-mapped-class
* Put postgres database in his own distribution with the good import
* Need improve alembic

Library to include
------------------

* Addons for sqlalchemy : http://sqlalchemy-utils.readthedocs.org/en/latest/installation.html
* full text search: https://pypi.python.org/pypi/SQLAlchemy-FullText-Search/0.2
* internationalisation: https://pypi.python.org/pypi/SQLAlchemy-i18n/0.8.2
* sqltap http://sqltap.inconshreveable.com, profiling and introspection for SQLAlchemy applications
* Crypt https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DatabaseCrypt
* profiling https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Profiling

Functionnality which need a sprint
----------------------------------

* Back Task
* Cron
* Tasks Management
* Event by messaging bus
* Import / Export
* Internalization
* Ancestor left / right
* Access Rules / Roles
