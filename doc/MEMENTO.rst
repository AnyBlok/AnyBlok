.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

MEMENTO
=======

Anyblok mainly depends on:

* Python 3.2+
* `SQLAlchemy <http://www.sqlalchemy.org>`_
* `Alembic <http://alembic.readthedocs.org/en/latest/>`_

Blok
----

A blok is a collection of source code files. These files are loaded in the registry
only if the blok state is ``installed``.

To declare a blok you have to:

1) Declare a Python package::

    The name of the module is not really significant
    --> Just create an ``__init__.py`` file

2) Declare a blok class in the ``__init__.py`` of the Python package::

    from anyblok.blok import Blok


    class MyBlok(Blok):
        """ Short description of the blok """
        ...
        version = '1.0.0'


Here are the available attributes for the blok:

+-----------------------+-----------------------------------------------------+
| Attribute             | Description                                         |
+=======================+=====================================================+
| ``__doc__``           | Short description of the blok (in the docstring)    |
+-----------------------+-----------------------------------------------------+
| ``version``           | the version of the blok (required because no value  |
|                       | by default)                                         |
+-----------------------+-----------------------------------------------------+
| ``autoinstall``       | boolean, if ``True`` this blok is automatically     |
|                       | installed                                           |
+-----------------------+-----------------------------------------------------+
| ``priority``          | installation order of the blok to installation      |
+-----------------------+-----------------------------------------------------+
| ``readme``            | Path of the 'readme' file of the blok, by default   |
|                       | ``README.rst``                                      |
+-----------------------+-----------------------------------------------------+
| ``required``          | List of the required dependancies for install       |
+-----------------------+-----------------------------------------------------+
| ``optional``          | List of the optional dependencies, their are        |
|                       | installed if they are found                         |
+-----------------------+-----------------------------------------------------+
| ``conflicting``       | List the blok which are not be installed to install |
|                       | this blok                                           |
+-----------------------+-----------------------------------------------------+
| ``conditionnal``      | If the bloks of this list ares installed the this   |
|                       | blok will be automaticly installed                  |
+-----------------------+-----------------------------------------------------+

And the methods that define blok behaviours:

+-------------------------------+---------------------------------------------+
| Method                        | Description                                 |
+===============================+=============================================+
| ``import_declaration_module`` | ``classmethod``, call to import all python  |
|                               | module which declare object from blok.      |
+-------------------------------+---------------------------------------------+
| ``reload_declaration_module`` | ``classmethod``, call to reload the import  |
|                               | all the python module which declare object  |
+-------------------------------+---------------------------------------------+
| ``update``                    | Action to do when the blok is being         |
|                               | install or updated. This method has one     |
|                               | argument ``latest_version`` (None for       |
|                               | install)                                    |
+-------------------------------+---------------------------------------------+
| ``uninstall``                 | Action to do when the blok is being         |
|                               | uninstalled                                 |
+-------------------------------+---------------------------------------------+
| ``load``                      | Action to do when the server starts         |
+-------------------------------+---------------------------------------------+
| ``pre_migration``             | Action to do when the blok is being         |
|                               | installed or updated to make some specific  |
|                               | migration, before auto migration.           |
|                               | This method has one argument                |
|                               | ``latest_version`` (None for install)       |
+-------------------------------+---------------------------------------------+
| ``post_migration``            | Action to do when the blok is being         |
|                               | installed or updated to make some specific  |
|                               | migration, after auto migration.            |
|                               | This method has one argument                |
|                               | ``latest_version`` (None for install)       |
+-------------------------------+---------------------------------------------+

And some facility:

+-------------------------------+---------------------------------------------+
| Method                        | Description                                 |
+===============================+=============================================+
| ``import_file``               | facility to import data                     |
+-------------------------------+---------------------------------------------+

.. note::

    The version 0.2.0 change the import and reload of the module python

3) Declare the entry point in the ``setup.py``::

    from setuptools import setup


    setup(
        ...
        entry_points={
            'bloks': [
                'web=anyblok_web_server.bloks.web:Web',
            ],
        },
        ...
    )

.. note::

    The version 0.4.0, required all the declaration of the bloks on the entry
    point **bloks**

Declaration
-----------

In AnyBlok, everything is a declaration (Model, Mixin, ...) and you have to
import the ``Declarations`` class::

    from anyblok.declarations import Declarations

The ``Declarations`` has two main methods

+---------------------+-------------------------------------------------------+
| Method name         | Description                                           |
+=====================+=======================================================+
| ``register``        | Add the declaration in the registry                   |
|                     | This method can be used as:                           |
|                     |                                                       |
|                     | * A function::                                        |
|                     |                                                       |
|                     |    class Foo:                                         |
|                     |        pass                                           |
|                     |                                                       |
|                     |    register(``Declarations.type``, cls_=Foo)          |
|                     |                                                       |
|                     | * A decorator::                                       |
|                     |                                                       |
|                     |    @register(``Declarations.type``)                   |
|                     |    class Foo:                                         |
|                     |        pass                                           |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| ``unregister``      | Remove an existing declaration from the registry.     |
|                     | This method is only used as a function::              |
|                     |                                                       |
|                     |    from ... import Foo                                |
|                     |                                                       |
|                     |    unregister(``Declarations.type``, cls_=Foo)        |
|                     |                                                       |
+---------------------+-------------------------------------------------------+

.. note::

    ``Declarations.type`` must be replaced by:

    * Model
    * ...

    ``Declarations.type`` defines the behaviour of the ``register`` and
    ``unregister`` methods

Model
-----

A Model is an AnyBlok class referenced in the registry. The registry is
hierarchical. The model ``Foo`` is accessed by ``registry.Foo`` and the model
``Foo.Bar`` is accessed by ``registry.Foo.Bar``.

To declare a Model you must use ``register``::

    from anyblok.declarations import Declarations


    register = Declarations.register
    Model = Declarations.Model


    @register(Model):
    class Foo:
        pass

The name of the model is defined by the name of the class (here ``Foo``).
The namespace of ``Foo`` is defined by the hierarchy under ``Model``. In this
example, ``Foo`` is in ``Model``, you can access at ``Foo`` by ``Model.Foo``.

.. warning::

    ``Model.Foo`` is not the ``Foo`` Model. It is an avatar of ``Foo`` only
    used for the declaration.

If you define the ``Bar`` model, under the ``Foo`` model, you should write::

    @register(Model.Foo)
    class Bar:
        """ Description of the model """
        pass

.. note::

    The description is used by the model System.Model to describe the model

The declaration name of ``Bar`` is ``Model.Foo.Bar``. The namespace of
``Bar`` in the registry is ``Foo.Bar``. The namespace of ``Foo`` in the
registry is ``Foo``::

    Foo = registry.Foo
    Bar = registry.Foo.Bar

Some models have a table in the database. The name of the table is by default the
namespace in lowercase with ``.`` replaced with ``.``.

.. note::

    The registry is accessible only in the method of the models::

        @register(Model)
        class Foo:

            def myMethod(self):
                registry = self.registry
                Foo = registry.Foo

The main goal of AnyBlok is not only to add models in the registry, but also
to easily overload these models. The declaration stores the Python class in
the registry. If one model already exist then the second declaration of this
model overloads the first model::

    @register(Model)
    class Foo:
        x = 1


    @register(Model)
    class Foo:
        x = 2


    ------------------------------------------

    Foo = registry.Foo
    assert Foo.x == 2

Here are the parameters of the ``register`` method for ``Model``:

+-------------+---------------------------------------------------------------+
| Param       | Description                                                   |
+=============+===============================================================+
| cls\_       | Define the real class if ``register`` is used as a            |
|             | function not as a decorator                                   |
+-------------+---------------------------------------------------------------+
| name\_      | Overload the name of the class::                              |
|             |                                                               |
|             |    @register(Model, name_='Bar')                              |
|             |    class Foo:                                                 |
|             |        pass                                                   |
|             |                                                               |
|             |   Declarations.Bar                                            |
|             |                                                               |
+-------------+---------------------------------------------------------------+
| tablename   | Overload the name of the table::                              |
|             |                                                               |
|             |    @register(Model, tablename='my_table')                     |
|             |    class Foo:                                                 |
|             |        pass                                                   |
|             |                                                               |
+-------------+---------------------------------------------------------------+
| is_sql_view | Boolean flag, which indicateis if the model is based on a SQL |
|             | view                                                          |
+-------------+---------------------------------------------------------------+
| tablename   | Define the real name of the table. By default the table name  |
|             | is the registry name without the declaration type, and with   |
|             | '.' replaced with '_'. This attribute is also used to map an  |
|             | existing table declared by a previous Model. Allowed values:  |
|             |                                                               |
|             | * str ::                                                      |
|             |                                                               |
|             |    @register(Model, tablename='foo')                          |
|             |    class Bar:                                                 |
|             |        pass                                                   |
|             |                                                               |
|             | * declaration ::                                              |
|             |                                                               |
|             |    @register(Model, tablename=Model.Foo)                      |
|             |    class Bar:                                                 |
|             |        pass                                                   |
|             |                                                               |
+-------------+---------------------------------------------------------------+

.. warning::

    Model can only inherit simple python class, Mixin or Model.


Non SQL Model
~~~~~~~~~~~~~

This is the default model. This model has no tables. It is used to
organize the registry or for specific process.::

    #register(Model)
    class Foo:
        pass

SQL Model
~~~~~~~~~

A ``SQL Model`` is a simple ``Model`` with ``Column`` or ``RelationShip``. For
each model, one table will be created.::

    @register(Model)
    class Foo:
        # SQL Model with mapped with the table ``foo``

        id = Integer(primary_key=True)
        # id is a column on the table ``foo``

.. warning:: Each SQL Model have to have got one or more primary key

In the case or you need to add some configuration in the SQLAlchemy class
attrinute:

* __table_args\_\_
* __mapper_args\_\_

you can use the next class methods

+--------------------+--------------------------------------------------------+
| method             | description                                            |
+====================+========================================================+
| define_table_args  | Add options for SQLAlchemy table build:                |
|                    |                                                        |
|                    | * Constraints on multiple columns                      |
|                    | * ...                                                  |
|                    |                                                        |
|                    | ::                                                     |
|                    |                                                        |
|                    |     @classmethod                                       |
|                    |     def define_table_args(cls, table_args, properties):|
|                    |         # table_args: tuple of the known               |
|                    |         #             __table_args\_\_                 |
|                    |         # properties: properties of the assembled model|
|                    |         #             columns, registry name           |
|                    |         return my_tuple_value                          |
|                    |                                                        |
+--------------------+--------------------------------------------------------+
| define_mapper_args | Add options for SQLAlchemy mappers build:              |
|                    |                                                        |
|                    | * polymorphisme                                        |
|                    | * ...                                                  |
|                    |                                                        |
|                    | ::                                                     |
|                    |                                                        |
|                    |     @classmethod                                       |
|                    |     def define_mapper_args(cls, mapper_args,           |
|                    |                            properties):                |
|                    |         # table_args: dict of the known                |
|                    |         #             __mapper_args\_\_                |
|                    |         # properties: properties of the assembled model|
|                    |         #             columns, registry name           |
|                    |         return my_dict_value                           |
|                    |                                                        |
+--------------------+--------------------------------------------------------+

.. note::

    New in 0.4.0

View Model
~~~~~~~~~~

A ``View Model`` as ``SQL Model``. Need the declaration of ``Column`` and / or
``RelationShip``. In the ``register`` the param ``is_sql_view`` must be
True and the ``View Model`` must define the ``sqlalchemy_view_declaration``
classmethod.::

    @register(Model, is_sql_view=True)
    class Foo:

        id = Integer(primary_key=True)
        name = String()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            from sqlalchemy.sql import select
            Model = cls.registry.System.Model
            return select([Model.id.label('id'), Model.name.label('name')])

``sqlalchemy_view_declaration`` must return a select query corresponding to the
request of the SQL view.

Column
------

To declare a ``Column`` in a model, add a column on the table of the model.::

    from anyblok.declarations import Declarations
    from anyblok.column import Integer, String


    @Declarations.register(Declaration.Model)
    class MyModel:

        id = Integer(primary_key=True)
        name = String()

.. note::

    Since the version 0.4.0 the ``Columns`` are not ``Declarations``

List of the column type:

 * ``DateTime``: use datetime.datetime, with pytz for the timezone
 * ``Decimal``: use decimal.Decimal
 * ``Float``
 * ``Time``: use datetime.time
 * ``BigInteger``
 * ``Boolean``
 * ``Date``: use datetime.date
 * ``Integer``
 * ``Interval``: use datetime.timedelta
 * ``LargeBinary``
 * ``SmallInteger``
 * ``String``
 * ``Text``
 * ``uString``
 * ``uText``
 * ``Selection``
 * ``Json``
 * ``Sequence``
 * ``Color``: use colour.Color
 * ``Password``: use sqlalchemy_utils.types.password.Password
 * ``UUID``: use uuid
 * ``URL``: use furl.furl

All the columns have the following optional parameters:

+----------------+------------------------------------------------------------+
| Parameter      | Description                                                |
+================+============================================================+
| label          | Label of the column, If None the label is the name of      |
|                | column capitalized                                         |
+----------------+------------------------------------------------------------+
| default        | define a default value for this column.                    |
|                |                                                            |
|                | ..warning::                                                |
|                |                                                            |
|                |     The default value depends of the column type           |
|                |                                                            |
|                | ..note::                                                   |
|                |                                                            |
|                |     Put the name of a classmethod to call it               |
|                |                                                            |
+----------------+------------------------------------------------------------+
| index          | boolean flag to define whether the column is indexed       |
+----------------+------------------------------------------------------------+
| nullable       | Defines if the column must be filled or not                |
+----------------+------------------------------------------------------------+
| primary_key    | Boolean flag to define if the column is a primary key or   |
|                | not                                                        |
+----------------+------------------------------------------------------------+
| unique         | Boolean flag to define if the column value must be unique  |
|                | or not                                                     |
+----------------+------------------------------------------------------------+
| foreign_key    | Define a foreign key on this column to another column of   |
|                | another model::                                            |
|                |                                                            |
|                |    @register(Model)                                        |
|                |    class Foo:                                              |
|                |        id : Integer(primary_key=True)                      |
|                |                                                            |
|                |    @register(Model)                                        |
|                |    class Bar:                                              |
|                |        id : Integer(primary_key=True)                      |
|                |        foo: Integer(foreign_key=Model.Foo.use('id'))       |
|                |                                                            |
|                | If the ``Model`` Declarations doesn't exist yet, you can   |
|                | use the regisrty name::                                    |
|                |                                                            |
|                |     foo: Integer(foreign_key='Model.Foo=>id'))             |
|                |                                                            |
+----------------+------------------------------------------------------------+
| db_column_name | String to define the real column name in the table,        |
|                | different from the model attribute name                    |
+----------------+------------------------------------------------------------+
| encrypt_key    | Crypt the column in the database. can take the values:     |
|                |                                                            |
|                | * a String ex: foo = String(encrypt_key='SecretKey')       |
|                | * a classmethod name on the model                          |
|                | * True value, search in the Configuration                  |
|                |   ``default_encrypt_key`` the value, they are no default.  |
|                |   if no value exist, an exception is raised                |
|                |                                                            |
|                | ..warning::                                                |
|                |                                                            |
|                |     The python package cryptography must be installed      |
|                |                                                            |
+----------------+------------------------------------------------------------+

Other attribute for ``String`` and ``uString``:

+-------------+---------------------------------------------------------------+
| Param       | Description                                                   |
+=============+===============================================================+
| ``size``    | Column size in the table                                      |
+-------------+---------------------------------------------------------------+

Other attribute for ``Selection``:

+----------------+------------------------------------------------------------+
| Param          | Description                                                |
+================+============================================================+
| ``size``       | column size in the table                                   |
+----------------+------------------------------------------------------------+
| ``selections`` | ``dict`` or ``dict.items`` to give the available key with  |
|                | the associate label                                        |
+----------------+------------------------------------------------------------+

Other attribute for ``Sequence``:

+--------------+--------------------------------------------------------------+
| Param        | Description                                                  |
+==============+==============================================================+
| ``size``     | column size in the table                                     |
+--------------+--------------------------------------------------------------+
| ``code``     | code of the sequence                                         |
+--------------+--------------------------------------------------------------+
| ``formater`` | formater of the sequence                                     |
+--------------+--------------------------------------------------------------+

Other attribute for ``Color``:

+----------------+------------------------------------------------------------+
| Param          | Description                                                |
+================+============================================================+
| ``size``       | column max size in the table                               |
+----------------+------------------------------------------------------------+

Other attribute for ``Password``:

+-------------------+---------------------------------------------------------+
| Param             | Description                                             |
+===================+=========================================================+
| ``size``          | password max size in the table                          |
+-------------------+---------------------------------------------------------+
| ``crypt_context`` | see the option for the python lib `passlib              |
|                   | <https://pythonhosted.org/passlib/lib/passlib.context.ht|
|                   | ml>`_                                                   |
+-------------------+---------------------------------------------------------+

..warning::

    The Password column can be found with the query meth:

Other attribute for ``UUID``:

+----------------+------------------------------------------------------------+
| Param          | Description                                                |
+================+============================================================+
| ``binary``     | Stores a UUID in the database natively when it can and     |
|                | falls back to a BINARY(16) or a CHAR(32)                   |
+----------------+------------------------------------------------------------+

RelationShip
------------

To declare a ``RelationShip`` in a model, add a RelationShip on the table of
the model.::

    from anyblok.declarations import Declarations
    from anyblok.column import Integer
    from anyblok.relationship import Many2One


    @Declarations.register(Declaration.Model)
    class MyModel:

        id = Integer(primary_key=True)


    @Declarations.register(Declaration.Model)
    class MyModel2:

        id = Integer(primary_key=True)
        mymodel = Many2One(model=Declaration.Model.MyModel)

.. note::

    Since the version 0.4.0 the ``RelationShip`` are not ``Declarations``

List of the RelationShip type:

* ``One2One``
* ``Many2One``
* ``One2Many``
* ``Many2Many``

Parameters of a ``RelationShip``:

+--------------------+--------------------------------------------------------+
| Param              | Description                                            |
+====================+========================================================+
| ``label``          | The label of the column                                |
+--------------------+--------------------------------------------------------+
| ``model``          | The remote model                                       |
+--------------------+--------------------------------------------------------+
| ``remote_columns`` | The column name on the remote model, if no remote      |
|                    | columns are defined the remote column will be the      |
|                    | primary column of the remote model                     |
+--------------------+--------------------------------------------------------+

Parameters of the ``One2One`` field:

+-------------------+---------------------------------------------------------+
| Param             | Description                                             |
+===================+=========================================================+
| ``column_names``  | Name of the local column.                               |
|                   | If the column doesn't exist then this column will be    |
|                   | created.                                                |
|                   | If no column name then the name will be 'tablename' +   |
|                   | '_' + name of the relationships                         |
+-------------------+---------------------------------------------------------+
| ``nullable``      | Indicates if the column name is nullable or not         |
+-------------------+---------------------------------------------------------+
| ``backref``       | Remote One2One link with the column name                |
+-------------------+---------------------------------------------------------+

Parameters of the ``Many2One`` field:

+-------------------+---------------------------------------------------------+
| Parameter         | Description                                             |
+===================+=========================================================+
| ``column_names``  | Name of the local column.                               |
|                   | If the column doesn't exist then this column will be    |
|                   | created.                                                |
|                   | If no column name then the name will be 'tablename' +   |
|                   | '_' + name of the relationships                         |
+-------------------+---------------------------------------------------------+
| ``nullable``      | Indicate if the column name is nullable or not          |
+-------------------+---------------------------------------------------------+
| ``one2many``      | Opposite One2Many link with this Many2one               |
+-------------------+---------------------------------------------------------+

Parameters of the ``One2Many`` field:

+-------------------+---------------------------------------------------------+
| Parameter         | Description                                             |
+===================+=========================================================+
| ``primaryjoin``   | Join condition between the relationship and the remote  |
|                   | column                                                  |
+-------------------+---------------------------------------------------------+
| ``many2one``      | Opposite Many2One link with this One2Many               |
+-------------------+---------------------------------------------------------+

Parameters of the ``Many2Many`` field:

+------------------------+----------------------------------------------------+
| Parameter              | Description                                        |
+========================+====================================================+
| ``join_table``         | many2many intermediate table between both models   |
+------------------------+----------------------------------------------------+
| ``m2m_remote_columns`` | Column name in the join table which have got the   |
|                        | foreign key to the remote model                    |
+------------------------+----------------------------------------------------+
| ``local_columns``      | Name of the local column which holds the foreign   |
|                        | key to the join table.                             |
|                        | If the column does not exist then this column will |
|                        | be created.                                        |
|                        | If no column name then the name will be 'tablename'|
|                        | + '_' + name of the relationship                   |
+------------------------+----------------------------------------------------+
| ``m2m_local_columns``  | Column name in the join table which holds the      |
|                        | foreign key to the model                           |
+------------------------+----------------------------------------------------+
| ``many2many``          | Opposite Many2Many link with this relationship     |
+------------------------+----------------------------------------------------+

.. note::

    Since 0.4.0, when the relationnal table is created by AnyBlok, the
    m2m_columns becomme foreign keys


Field
-----

To declare a ``Field`` in a model, add a Field on the Model, this is not a
SQL column.::

    from anyblok.declarations import Declarations
    from anyblok.field import Function
    from anyblok.column import Integer


    @Declarations.register(Declaration.Model)
    class MyModel:

        id = Integer(primary_key=True)
        first_name = String()
        last_name = String()
        name = Function(fget='fget', fset='fset', fdel='fdel', fexpr='fexpr')

        def fget(self):
            return '{0} {1}'.format(self.first_name, self.last_name)

        def fset(self, value):
            self.first_name, self.last_name = value.split(' ', 1)

        def fdel(self):
            self.first_name = self.last_name = None

        @classmethod
        def fexpr(cls):
            return func.concat(cls.first_name, ' ', cls.last_name)

List of the ``Field`` type:

* ``Function``

Parameters for ``Field.Function``

+-------------------+---------------------------------------------------------+
| Parameter         | Description                                             |
+===================+=========================================================+
| ``fget``          | name of the method to call to get the value of field::  |
|                   |                                                         |
|                   |   def fget(self):                                       |
|                   |       return '{0} {1}'.format(self.first_name,          |
|                   |                               self.last_name)           |
|                   |                                                         |
+-------------------+---------------------------------------------------------+
| ``fset``          | name of the method to call to set the value of field::  |
|                   |                                                         |
|                   |   def fset(self):                                       |
|                   |       self.first_name, self.last_name = value.split(' ',|
|                   |                                                     1)  |
|                   |                                                         |
+-------------------+---------------------------------------------------------+
| ``fdel``          | name of the method to call to del the value of field::  |
|                   |                                                         |
|                   |   def fdel(self):                                       |
|                   |       self.first_name = self.last_name = None           |
|                   |                                                         |
+-------------------+---------------------------------------------------------+
| ``fexp``          | name of the class method to call to filter on the       |
|                   | field::                                                 |
|                   |                                                         |
|                   |   @classmethod                                          |
|                   |   def fexp(self):                                       |
|                   |       return func.concat(cls.first_name, ' ',           |
|                   |                          cls.last_name)                 |
|                   |                                                         |
+-------------------+---------------------------------------------------------+

Mixin
-----

A Mixin looks like a Model, but has no tables. A Mixin adds behaviour to
a Model with Python inheritance::

    @register(Mixin)
    class MyMixin:

        def foo():
            pass

    @register(Model)
    class MyModel(Mixin.MyMixin):
        pass

    ----------------------------------

    assert hasattr(registry.MyModel, 'foo')


If you inherit a mixin, all the models previously using the base mixin also benefit
from the overload::

    @register(Mixin)
    class MyMixin:
        pass

    @register(Model)
    class MyModel(Mixin.MyMixin):
        pass

    @register(Mixin)
    class MyMixin:

        def foo():
            pass

    ----------------------------------

    assert hasattr(registry.MyModel, 'foo')


SQL View
--------

An SQL view is a model, with the argument ``is_sql_view=True`` in the
register. and the classmethod ``sqlalchemy_view_declaration``::

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, is_sql_view=True)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            """ This method must return the query of the view """
            T1 = cls.registry.T1
            T2 = cls.registry.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)


Core
----

``Core`` is a low level set of declarations for all the Models of AnyBlok. ``Core`` adds
general behaviour to the application.

.. warning::

    Core can not inherit Model, Mixin, Core, or other declaration type.

Base
~~~~

Add a behaviour in all the Models, Each Model inherits Base. For instance, the
``fire`` method of the event come from ``Core.Base``.

::

    from anyblok import Declarations


    @Declarations.register(Declarations.Core)
    class Base:
        pass

SqlBase
~~~~~~~

Only the Models with ``Field``, ``Column``, ``RelationShip`` inherits ``Core.SqlBase``.
For instance, the ``insert`` method only makes sense for the ``Model`` with a table.

::

    from anyblok import Declarations


    @Declarations.register(Declarations.Core)
    class SqlBase:
        pass

SqlViewBase
~~~~~~~~~~~

Like ``SqlBase``, only the ``SqlView`` inherits this ``Core`` class.

::

    from anyblok import Declarations


    @Declarations.register(Declarations.Core)
    class SqlViewBase:
        pass

Query
~~~~~

Overloads the SQLAlchemy ``Query`` class.

::

    from anyblok import Declarations


    @Declarations.register(Declarations.Core)
    class Query
        pass

Session
~~~~~~~

Overloads the SQLAlchemy ``Session`` class.

::

    from anyblok import Declarations


    @Declarations.register(Declarations.Core)
    class Session
        pass

InstrumentedList
~~~~~~~~~~~~~~~~

::

    from anyblok import Declarations


    @Declarations.register(Declarations.Core)
    class InstrumentedList
        pass

``InstrumentedList`` is the class returned by the Query for all the list result
like:

* query.all()
* relationship list (Many2Many, One2Many)

Adds some features like getting a specific property or calling a method on all
the elements of the list::

    MyModel.query().all().foo(bar)

Sharing a table between more than one model
-------------------------------------------

SQLAlchemy allows two methods to share a table between two or more mapping
class:

* Inherit an SQL Model in a non-SQL Model::

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Test2(Model.Test):
        pass

    ----------------------------------------

    t1 = Test1.insert(name='foo')
    assert Test2.query().filter(Test2.id == t1.id,
                                Test2.name == t1.name).count() == 1

* Share the ``__table__``.
    AnyBlok cannot give the table at the declaration, because the table does not
    exist yet. But during the assembly, if the table exists and the model
    has the name of this table, AnyBlok directly links the table. To
    define the table you must use the named argument ``tablename`` in the
    ``register``

    ::

        @register(Model)
        class Test:
            id = Integer(primary_key=True)
            name = String()

        @register(Model, tablename=Model.Test)
        class Test2:
            id = Integer(primary_key=True)
            name = String()

        ----------------------------------------

        t1 = Test1.insert(name='foo')
        assert Test2.query().filter(Test2.id == t1.id,
                                    Test2.name == t1.name).count() == 1

    .. warning::
        There are no checks on the existing columns.

Sharing a view between more than one model
------------------------------------------

Sharing a view between two Models is the merge between:

* Creating a View Model
* Sharing the same table between more than one model.

.. warning::

    For the view you must redined the column in the Model corresponding to the view
    with inheritance or simple Share by tablename

Specific behaviour
------------------

AnyBlok implements some facilities to help developers

Column encryption
~~~~~~~~~~~~~~~~~

You can encrypt some columns to protect them. The python package cryptography
must be installed::

    pip install cryptography

Use the encrypt_key attribute on the column to define the key of cryptography::

    @register(Model)
    class MyModel:

        # define the specific encrypt_key
        encrypt_column_1 = String(encrypt_key='SecretKey')

        # Use the default encrypt_key
        encrypt_column_2 = String(encrypt_key=Configuration.get('default_encrypt_key')
        encrypt_column_3 = String(encrypt_key=True)

        # Use the class method to get encrypt_key
        encrypt_column_1 = String(encrypt_key='get_encrypt_key')

        @classmethod
        def get_encrypt_key(cls):
            return 'SecretKey'

The encryption works for any Columns.

Cache
~~~~~

The cache allows to call a method more than once without having any difference
in the result. But the cache must also depend on the registry database and the
model. The cache of anyblok can be put on a Model, a Core or a Mixin method. If
the cache is on a Core or a Mixin then the usecase depends on the registry name
of the assembled model.

Use ``cache`` or ``classmethod_cache`` to apply a cache on a method::

    from anyblok.declarations import cache, classmethod_cache

.. warning::

    ``cache`` depend of the instance, if you want add a cache for
    any instance you must use ``classmethod_cache``

Cache the method of a Model::

    @register(Model)
    class Foo:

        @classmethod_cache()
        def bar(cls):
            import random
            return random.random()


    -----------------------------------------

    assert Foo.bar() == Foo.bar()


Cache the method coming from a Mixin::

    @register(Mixin)
    class MFoo:

        @classmethod_cache()
        def bar(cls):
            import random
            return random.random()

    @register(Model)
    class Foo(Mixin.MFoo):
        pass

    @register(Model)
    class Foo2(Mixin.MFoo):
        pass


    -----------------------------------------

    assert Foo.bar() == Foo.bar()
    assert Foo2.bar() == Foo2.bar()
    assert Foo.bar() != Foo2.bar()


Cache the method coming from a Mixin::

    @register(Core)
    class Base

        @classmethod_cache()
        def bar(cls):
            import random
            return random.random()

    @register(Model)
    class Foo:
        pass

    @register(Model)
    class Foo2:
        pass


    -----------------------------------------

    assert Foo.bar() == Foo.bar()
    assert Foo2.bar() == Foo2.bar()
    assert Foo.bar() != Foo2.bar()

Event
~~~~~

Simple implementation of a synchronous ``event`` for AnyBlok or SQLAlchemy::


    @register(Model)
    class Event:
        pass

    @register(Model)
    class Test:

            x = 0

            @listen(Model.Event, 'fireevent')
            def my_event(cls, a=1, b=1):
                cls.x = a * b

    ---------------------------------------------

    registry.Event.fire('fireevent', a=2)
    assert registry.Test.x == 2

.. note::

    The decorated method is seen as a classmethod

This API gives:

* a decorator ``listen`` which binds the decorated method to the event.
* ``fire`` method with the following parameters (Only for AnyBlok event):
    - ``event``: string name of the event
    - ``*args``: positionnal arguments to pass att the decorated method
    - ``**kwargs``: named argument to pass at the decorated method

It is possible to overload an existing event listener, just by overloading the
decorated method::

    @register(Model)
    class Test:

        @classmethod
        def my_event(cls, **kwarg):
            res = super(Test, cls).my_event(**kwargs)
            return res * 2

    ---------------------------------------------

    registry.Event.fire('fireevent', a=2)
    assert registry.Test.x == 4

.. warning::

    The overload does not take the ``listen`` decorator but the
    classmethod decorator, because the method name is already seen as an
    event listener

Some of the Attribute events of the Mapper events are implemented. See the
SQLAlchemy ORM Events http://docs.sqlalchemy.org/en/latest/orm/events.html#orm-events

Hybrid method
~~~~~~~~~~~~~

Facility to create an SQLAlchemy hybrid method. See this page:
http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html#module-sqlalchemy.ext.hybrid

AnyBlok allows to define a hybrid_method which can be overloaded, because the
real sqlalchemy decorator is applied after assembling in the last overload
of the decorated method::

    from anyblok.declarations import hybrid_method

    @register(Model)
    class Test:

        @hybrid_method
        def my_hybrid_method(self):
            return ...

Pre-commit hook
~~~~~~~~~~~~~~~

It is possible to call specific classmethods just before the commit of the
session::

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        val = Integer(default=0)

        @classmethod
        def method2call_just_before_the_commit(cls):
            pass

    -----------------------------------------------------

    registry.Test.precommit_hook('method2call_just_before_the_commit')


Aliased
~~~~~~~

Facility to create an SQL alias for the SQL query by the ORM::

    select * from my_table the_table_alias.

This facility is given by SQLAlchemy, and anyblok adds this functionnality
directly in the Model::

    BlokAliased = registry.System.Blok.aliased()

.. note:: See this page:
    http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.aliased
    to know the parameters of the ``aliased`` method

    .. warning:: The first arg is already passed by AnyBlok

Get the registry
~~~~~~~~~~~~~~~~

You can get a Model by the registry in any method of Models::

    Model = self.registry.System.Model
    assert Model.__registry_name__ == 'Model.System.Model'

Get the current environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current environment is saved in the main thread. You can add a value to
the current Environment::

    self.Env.set('My var', 'one value')

You can get a value from the current Environment::

    myvalue = self.Env.get('My var', defaul="My default value")

.. note::

    The environment is as a dict the value can be an instance of any type

Initialize some data by entry point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

the entry point ``anyblok.init`` allow to define function, ``ìnit_function``
in this example::

    setup(
        ...
        entry_points={
            'anyblok.init': [
                'my_function=path:init_function',
            ],
        },
    )

In the path the init_function must be defined::

    def init_function(unittest=False):
        ...

..warning::

    Use unittest parameter to defined if the function must be call
    or not

Plugin
------

Plugin is used for the low level, it is not use in the bloks, because the model
can be overload by the declaration.

Define a new plugin
~~~~~~~~~~~~~~~~~~~

A plugin can be a class or a function::

    class MyPlugin:
        pass

Add the plugin definition in the configuration::

    @Configuration.add('plugins')
    def add_plugins(self, group)
        group.add_argument('--my-option', dest='plugin_name',
                           type=AnyBlokPlugin,
                           default='path:MyPlugin')

Use the plugin::

    plugin = Configuration.get('plugin_name')
