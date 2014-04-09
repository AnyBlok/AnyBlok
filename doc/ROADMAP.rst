ROADMAP
=======

Next step
---------

* Add Migration Class with Unittest: see alembic: http://alembic.readthedocs.org/en/latest/
* Do documentation

To implement
------------

* core.query : implement a method to subclass one method for automaticly where clause in model https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/PreFilteredQuery
* Add Blok group as "Category" or "Blok group"
* Make a registry reload to update registry without destroy the curent registry and create a new(Protect the session)
* Add RelationShip model in anyblok-core and refatore the get column http://docs.sqlalchemy.org/en/latest/faq.html#how-do-i-get-a-list-of-all-columns-relationships-mapped-attributes-etc-given-a-mapped-class
* Refactor the m2m, o2m, m2o, o2o. Allow to have more than one primary key
* Refactor split load method of registry and unit test all part

Fix me
------

* Enum Column doesn't work, see http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/
  or https://pypi.python.org/pypi/SQLAlchemy-Enum-Dict/0.1.2
* Add the posibility to add a nullable column by migration

Library to include
------------------

* Addons for sqlalchemy : http://sqlalchemy-utils.readthedocs.org/en/latest/installation.html
* gevent https://pypi.python.org/pypi/sqlalchemy-gevent/0.1
* full text search: https://pypi.python.org/pypi/SQLAlchemy-FullText-Search/0.2
* internationalisation: https://pypi.python.org/pypi/SQLAlchemy-i18n/0.8.2
* shematisation of https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/SchemaDisplay
* sqltap http://sqltap.inconshreveable.com, profiling and introspection for SQLAlchemy applications
* SchemaDisplay: not realy a library, just a poc for the moment https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/SchemaDisplay
* SQL View https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Views
* Ajouter automatiquement m2o et o2m lors de la declaration d'une foreign key https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/AutoRelationships
* Crypt https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DatabaseCrypt
* profiling https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Profiling
* json column https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/JSONColumn
