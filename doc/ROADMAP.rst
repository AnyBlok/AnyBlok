ROADMAP
=======

Next step
---------

* Improve Migration Class with Unittest: see alembic: http://alembic.readthedocs.org/en/latest/
* Do documentation
* ADD unittest:
    - anyblok_core system

To implement
------------

* Add Blok group as "Category" or "Blok group"
* Make a registry reload to update registry without destroy the curent registry and create a new(Protect the session)
* Add RelationShip model in anyblok-core and refatore the get column http://docs.sqlalchemy.org/en/latest/faq.html#how-do-i-get-a-list-of-all-columns-relationships-mapped-attributes-etc-given-a-mapped-class
* Put postgres databas in this own distribution with the good import

Library to include
------------------

* Addons for sqlalchemy : http://sqlalchemy-utils.readthedocs.org/en/latest/installation.html
* full text search: https://pypi.python.org/pypi/SQLAlchemy-FullText-Search/0.2
* internationalisation: https://pypi.python.org/pypi/SQLAlchemy-i18n/0.8.2
* sqltap http://sqltap.inconshreveable.com, profiling and introspection for SQLAlchemy applications
* Crypt https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DatabaseCrypt
* profiling https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Profiling
* json column https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/JSONColumn
* Enum Column doesn't work, see http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/
  or https://pypi.python.org/pypi/SQLAlchemy-Enum-Dict/0.1.2


Web client
----------

* http://www.javascriptkit.com/javatutors/closuresleak/index.shtml
* http://www.javascriptkit.com/javatutors/crossmenu.shtml
* cms https://github.com/Kotti/Kotti

Functionnality which need a sprint
----------------------------------

* Back Task
* Cron
* Tasks Management
* Event
* Event by messaging bus
* Import / Export 
