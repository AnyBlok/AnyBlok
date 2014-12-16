MEMENTO
=======

Anyblok is a framework write with:

* ``python 3.3``
* ``sqlalchemy``
* ``alembic``

All the implementation need with AnyBlok is presented here

Blok
----

A blok is a set of source code files. These files are loaded in the registry
only if the blok have this state equal at ``installed``.

To declare a blok you have to:

1) Declare a python module::

    ``the name of the module is not really important``
    --> __init__.py

2) Declare a blok class in the __init__ of the python module::

    from anyblok.blok import Blok


    class MyBlok(Blok):
        """ Short description of the blok """
        ...
        version = '1.0.0'


These are the options to apply at your blok

+-----------------------+-----------------------------------------------------+
| Name of the option    | Descriptions                                        |
+=======================+=====================================================+
|  ``__doc__``          | Short description of the blok                       |
+-----------------------+-----------------------------------------------------+
| ``version``           | the version of the blok(required because no value   |
|                       | by default)                                         |
+-----------------------+-----------------------------------------------------+
| ``autoinstall``       | boolean, if ``True`` this blok is automaticaly      |
|                       | installed                                           |
+-----------------------+-----------------------------------------------------+
| ``priority``          | order of the blok to installation                   |
+-----------------------+-----------------------------------------------------+
| ``readme``            | Readme file path of the blok, by default            |
|                       | ``README.rst``                                      |
+-----------------------+-----------------------------------------------------+

And the method defined blok behaviours

+-------------------------+---------------------------------------------------+
| Method name             | Description                                       |
+=========================+===================================================+
| ``clean_before_reload`` | ``classmethod``, call before python reload of the |
|                         | blok, use only if an action must be execute       |
|                         | before reload the blok                            |
+-------------------------+---------------------------------------------------+
| ``update``              | Action to do when the blok is installing or       |
|                         | updating, this method has got one argument        |
|                         | ``latest_version`` (None for install)             |
+-------------------------+---------------------------------------------------+
| ``uninstall``           | Action to do when the blok is uninstalled         |
+-------------------------+---------------------------------------------------+
| ``load``                | Action to do when the server start                |
+-------------------------+---------------------------------------------------+

3) Declare the entry point in the setup::

    from setuptools import setup


    setup(
        ...
        entry_points={
            'AnyBlok': [
                'web=anyblok_web_server.bloks.web:Web',
            ],
        },
        ...
    )

Declaration
-----------

In AnyBlok, all is declarations:

* Model
* Column
* ...

All is declaration and you have to import the ``Declarations`` class::

    from anyblok.declarations import Declarations

The ``Declarations`` have got two main method

+---------------------+-------------------------------------------------------+
| Method name         | Description                                           |
+=====================+=======================================================+
| ``target_registry`` | Add one declarations in the description of the blok.  |
|                     | This method can be used as:                           |
|                     |                                                       |
|                     | * A function::                                        |
|                     |                                                       |
|                     |    class Foo:                                         |
|                     |        pass                                           |
|                     |                                                       |
|                     |    target_registry(``Declarations.type``, cls_=Foo    |
|                     |                                                       |
|                     | * A decorator::                                       |
|                     |                                                       |
|                     |    @target_registry(``Declarations.type``)            |
|                     |    class Foo:                                         |
|                     |        pass                                           |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| ``remove_registry`` | Remove an existing declarations of whatever blok. This|
|                     | method is only used as a function::                   |
|                     |                                                       |
|                     |    from ... import Foo                                |
|                     |                                                       |
|                     |    remove_registry(``Declarations.type``, cls_=Foo)   |
|                     |                                                       |
+---------------------+-------------------------------------------------------+

.. note::

    ``Declarations.type`` must be replaced by:

    * Model
    * Column
    * ...

    ``Declarations.type`` define the behaviour of the ``target_registry`` and
    ``remove_registry`` methods

Each object which need this declarations define the need to used these methods

Model
-----

A ``Model`` is an AnyBlok ``class`` referenced in the registry. The registry is
hierarchical. The model ``Foo`` is accessed by ``registry.Foo`` and the model
``Foo.Bar`` is accessed by ``registry.Foo.Bar``.

To declare a Model you have tu use ``target_registry``::

    from anyblok.declarations import Declarations


    target_registry = Declarations.target_registry
    Model = Declarations.Model


    @target_registry(Model):
    class Foo:
        pass

The name of the model is defined by the name of the class, here it is ``Foo``.
The namespace of ``Foo`` id defined by the hierarchie in ``Model``. In this
example, ``Foo`` is in ``Model``, you can access at ``Foo`` by ``Model.Foo``.

.. warning::

    ``Model.Foo`` is not the ``Foo`` Model. it is an avatar of ``Foo`` only use
    for the declaration.

If you define the ``Bar`` model, under the ``Foo`` model, you should write::

    @target_registry(Model.Foo)
    class Bar:
        """ Description of the model """
        pass

.. note::

    The description is used by the model System.Model to describe the model

The declaration's name of ``Bar`` is ``Model.Foo.Bar``. The namespace of
``Bar`` in the registry is ``Foo.Bar``. The namespace of ``Foo`` in the
registry is ``Foo``::

    Foo = registry.Foo
    Bar = registry.Foo.Bar

Some model have got a table in the database. The table's name is by default the
namespace in lower and with ``-`` which replace ``.``.

.. note::

    The registry is accessible only in the method of the models::

        @target_registry(Model)
        class Foo:

            def myMethod(self):
                registry = self.registry
                Foo = registry.Foo

The main goal of AnyBlok is not only to add models in the registry, It is also
to overload easylly these models. The declaration, record the python class in
the registry, if one model already exist then the second declaration of this
model overload the first model::

    @target_registry(Model)
    class Foo:
        x = 1


    @target_registry(Model)
    class Foo:
        x = 2


    ------------------------------------------

    Foo = registry.Foo
    assert Foo.x == 2

These are the params of the ``target_registry`` method for ``Model``

+-------------+---------------------------------------------------------------+
| Param       | Description                                                   |
+=============+===============================================================+
| cls\_       | Define the real class if ``target_registry`` is used as a     |
|             | function not as a decorator                                   |
+-------------+---------------------------------------------------------------+
| name\_      | Overload the name of the class::                              |
|             |                                                               |
|             |    @target_registry(Model, name_='Bar')                       |
|             |    class Foo:                                                 |
|             |        pass                                                   |
|             |                                                               |
|             |   Declarations.Bar                                            |
|             |                                                               |
+-------------+---------------------------------------------------------------+
| tablename   | Overload the name of the table::                              |
|             |                                                               |
|             |    @target_registry(Model, tablename='my_table')              |
|             |    class Foo:                                                 |
|             |        pass                                                   |
|             |                                                               |
+-------------+---------------------------------------------------------------+
| is_sql_view | Boolean flag, which indicate if the model is based on a sql   |
|             | view                                                          |
+-------------+---------------------------------------------------------------+
| tablename   | Define the realname of the table. By default the table name   |
|             | registry name without the declaration type, and with the '.'  |
|             | replaced by '_'. This attibut is also used to map an existing |
|             | table declared by a previous Model. The allow values are :    |
|             |                                                               |
|             | * str ::                                                      |
|             |                                                               |
|             |    @target_registry(Model, tablename='foo')                   |
|             |    class Bar:                                                 |
|             |        pass                                                   |
|             |                                                               |
|             | * declaration ::                                              |
|             |                                                               |
|             |    @target_registry(Model, tablename=Model.Foo)               |
|             |    class Bar:                                                 |
|             |        pass                                                   |
|             |                                                               |
+-------------+---------------------------------------------------------------+

No SQL Model
~~~~~~~~~~~~

It is the default model. This model have got any table. It is used to
organize the registry or for specific process.::

    #target_registry(Model)
    class Foo:
        pass

SQL Model
~~~~~~~~~

A ``SQL Model`` is a simple ``Model`` with ``Column`` or ``RelationShip``. For
each models, one table will be created.::

    @target_registry(Model)
    class Foo:
        # SQL Model with mapped with the table ``foo``

        id = Integer(primary_key=True)
        # id is a column on the table ``foo``

.. warning:: Each SQL Model have to have got one or more primary key

View Model
~~~~~~~~~~

A ``View Model`` as ``SQL Model``, need the declaration of ``Column`` and / or
``RelationShip``. In the ``target_registry`` the param ``is_sql_view`` have to
flag at True value and the ``View Model`` must define the classmethod
``sqlalchemy_view_declaration``.::

    @target_registry(Model, is_sql_view=True)
    class Foo:

        id = Integer(primary_key=True)
        name = String()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            from sqlalchemy.sql import select
            Model = cls.registry.System.Model
            return select([Model.id.label('id'), Model.name.label('name')])

``sqlalchemy_view_declaration`` must return a select query to apply to create
a SQL view?

Column
------

To declare a ``Column`` in a model, add a column on the table of the model.
All the column type are in the ``Declarations``::

    from anyblok.declarations import Declarations


    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @Declarations.target_registry(Declaration.Model)
    class MyModel:

        id = Integer(primary_key=True)
        name = String()

List of the ``Déclarations`` of the column type:

 * ``DateTime``: use datetime.datetime
 * ``Decimal``: use decimal.Decimal
 * ``Float``
 * ``Time``: use datetime.time
 * ``BigInteger``
 * ``Boolean``
 * ``Date``: use datetime.date
 * ``Integer``
 * ``Interval``: use the datetime.timedelta
 * ``LargeBinary``
 * ``SmallInteger``
 * ``String``
 * ``Text``
 * ``uString``
 * ``uText``
 * ``Selection``
 * ``Json``

 All the columns have got the this params:

+-------------+---------------------------------------------------------------+
| Param       | Description                                                   |
+=============+===============================================================+
| label       | Label of the column, If None the label is the name of column  |
|             | capitalized                                                   |
+-------------+---------------------------------------------------------------+
| default     | define a default value for this column.                       |
|             |                                                               |
|             | ..warning:: the default value depend of the column type       |
+-------------+---------------------------------------------------------------+
| index       | boolean flag to define if the column is indexed               |
+-------------+---------------------------------------------------------------+
| nullable    | Define if the column must be filled or not                    |
+-------------+---------------------------------------------------------------+
| primary_key | Boolean flag to define if the column is primary key or not    |
+-------------+---------------------------------------------------------------+
| unique      | Boolean flag to define if the column value must be unique or  |
|             | not                                                           |
+-------------+---------------------------------------------------------------+
| foreign_key | Define a foreign key on this column to another column form    |
|             | another model::                                               |
|             |                                                               |
|             |    @target_registry(Model)                                    |
|             |    class Foo:                                                 |
|             |        id : Integer(primary_key=True)                         |
|             |                                                               |
|             |    @target_registry(Model)                                    |
|             |    class Bar:                                                 |
|             |        id : Integer(primary_key=True)                         |
|             |        foo: Integer(foreign_key=(Model.Foo, 'id'))            |
|             |                                                               |
+-------------+---------------------------------------------------------------+

Other attribute for ``String`` and ``uString``:

+-------------+---------------------------------------------------------------+
| Param       | Description                                                   |
+=============+===============================================================+
| ``size``    | Column size in the bdd                                        |
+-------------+---------------------------------------------------------------+

Other attribute for ``Selection``:

+----------------+------------------------------------------------------------+
| Param          | Description                                                |
+================+============================================================+
| ``size``       | column size in the bdd                                     |
+----------------+------------------------------------------------------------+
| ``selections`` | ``dict`` or ``dict.items`` to list the available key with  |
|                | the associate label                                        |
+----------------+------------------------------------------------------------+

RelationShip
------------

To declare a ``RelationShip`` in a model, add a RelationShip on the table of
the model. All the RelationShip type are in the ``Declarations``::

    from anyblok.declarations import Declarations


    Integer = Declarations.Column.Integer
    Many2One = Declarations.RelationShip.Many2One

    @Declarations.target_registry(Declaration.Model)
    class MyModel:

        id = Integer(primary_key=True)

    @Declarations.target_registry(Declaration.Model)
    class MyModel2:

        id = Integer(primary_key=True)
        mymodel = Many2One(model=Declaration.Model.MyModel)

List of the ``Déclarations`` of the RelationShip type:

* ``One2One``
* ``Many2One``
* ``One2Many``
* ``Many2Many``

Params for RelationShip:

+-------------------+---------------------------------------------------------+
| Param             | Description                                             |
+===================+=========================================================+
| ``label``         | The label of the column                                 |
+-------------------+---------------------------------------------------------+
| ``model``         | The remote model                                        |
+-------------------+---------------------------------------------------------+
| ``remote_column`` | The column name on the remote model, if any remote      |
|                   | column is filled the the remote column will be the      |
|                   | primary column of the remote model                      |
+-------------------+---------------------------------------------------------+

Params for ``One2One``:

+-------------------+---------------------------------------------------------+
| Param             | Description                                             |
+===================+=========================================================+
| ``column_name``   | Name of the local column.                               |
|                   | If the column doesn't exist then this column will be    |
|                   | created.                                                |
|                   | If any column name then the name will be 'tablename' +  |
|                   | '_' + name of the relation ship                         |
+-------------------+---------------------------------------------------------+
| ``nullable``      | Indicate if the column name is nullable or not          |
+-------------------+---------------------------------------------------------+
| ``backref``       | Remote One2One link with the column name                |
+-------------------+---------------------------------------------------------+

Params for ``Many2One``:

+-------------------+---------------------------------------------------------+
| Param             | Description                                             |
+===================+=========================================================+
| ``column_name``   | Name of the local column.                               |
|                   | If the column doesn't exist then this column will be    |
|                   | created.                                                |
|                   | If any column name then the name will be 'tablename' +  |
|                   | '_' + name of the relation ship                         |
+-------------------+---------------------------------------------------------+
| ``nullable``      | Indicate if the column name is nullable or not          |
+-------------------+---------------------------------------------------------+
| ``one2many``      | Opposite One2Many link with this Many2one               |
+-------------------+---------------------------------------------------------+

Params for ``One2Many``:

+-------------------+---------------------------------------------------------+
| Param             | Description                                             |
+===================+=========================================================+
| ``primaryjoin``   | Join condition between the relation ship and the remote |
|                   | column                                                  |
+-------------------+---------------------------------------------------------+
| ``many2one``      | Opposite Many2One link with this One2Many               |
+-------------------+---------------------------------------------------------+

Params for ``Many2Many``:

+-----------------------+-----------------------------------------------------+
| Param                 | Description                                         |
+=======================+=====================================================+
| ``join_table``        | many2many link table between both models            |
+-----------------------+-----------------------------------------------------+
| ``m2m_remote_column`` | Column name in the join table which have got the    |
|                       | foreign key to the remote model                     |
+-----------------------+-----------------------------------------------------+
| ``local_column``      | Name of the local column which have got the foreign |
|                       | key to the join table.                              |
|                       | If the column doesn't exist then this column will be|
|                       | created.                                            |
|                       | If any column name then the name will be 'tablename'|
|                       | + '_' + name of the relation ship                   |
+-----------------------+-----------------------------------------------------+
| ``m2m_local_column``  | Column name in the join table which have got the    |
|                       | foreign key to the model                            |
+-----------------------+-----------------------------------------------------+
| ``many2many``         | Opposite Many2Many link with this relation ship     |
+-----------------------+-----------------------------------------------------+

Field
-----

To declare a ``Field`` in a model, add a Field on the Model, this is not a
SQL column. All the Field type are in the ``Declarations``::

    from anyblok.declarations import Declarations


    Integer = Declarations.Column.Integer
    Fuction = Declarations.Field.Function

    @Declarations.target_registry(Declaration.Model)
    class MyModel:

        id = Integer(primary_key=True)
        myid = Function(fget='get_my_id')

        def get_my_id(self):
            return self.id

List of the ``Déclarations`` of the Field type:

* ``Function``

Params for ``Field.Function``

+-------------------+---------------------------------------------------------+
| Param             | Description                                             |
+===================+=========================================================+
| ``fget``          | method name to call to get the falue of field function::|
|                   |                                                         |
|                   |   def fget(self):                                       |
|                   |       return self.id                                    |
|                   |                                                         |
+-------------------+---------------------------------------------------------+
| ``model``         | The remote model                                        |
+-------------------+---------------------------------------------------------+
| ``remote_column`` | The column name on the remote model, if any remote      |
|                   | column is filled the the remote column will be the      |
|                   | primary column of the remote model                      |
+-------------------+---------------------------------------------------------+

Mixin
-----

Mixin look like Model, but they have any table. Mixin add behaviour at
Model by python inherit::

    @target_registry(Mixin)
    class MyMixin:

        def foo():
            pass

    @target_registry(Model)
    class MyModel(Mixin.MyMixin):
        pass

    ----------------------------------

    assert hasattr(registry.MyModel, 'foo')


In the assembling of the bases, if one base inherit of a mixin declaration
then all the bases of this mixin declaration replace the mixine declaration.
This behaviour allow to inherit one mixin and all the model which inherit this
mixin before the overload, get the overload too::

    @target_registry(Mixin)
    class MyMixin:
        pass

    @target_registry(Model)
    class MyModel(Mixin.MyMixin):
        pass

    @target_registry(Mixin)
    class MyMixin:

        def foo():
            pass

    ----------------------------------

    assert hasattr(registry.MyModel, 'foo')


SQL View
--------

SQL view is a model, with the argument ``is_sql_view=True`` in the
target_registry. and the classmethod ``sqlalchemy_view_declaration``::

    @target_registry(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model, is_sql_view=True)
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

Core is a low level for all Model of AnyBlok. Core add general behaviour of
the application.

Base
~~~~

Add a behaviour in all the Model, Each Model inherit of Base. for example, the
``fire`` method of the event come from Base core.

::

    from anyblok import Declarations


    @Declarations.target_registry(Declarations.Core)
    class Base:
        pass

SqlBase
~~~~~~~

Only the Model with ``Field``, ``Column``, ``RelationShip`` inherit SqlBase.
Because the method ``insert`` have interest only for the ``Model`` with a table

::

    from anyblok import Declarations


    @Declarations.target_registry(Declarations.Core)
    class SqlBase:
        pass

SqlViewBase
~~~~~~~~~~~

As SqlBase, only the SqlView inherit this ``Core``.

::

    from anyblok import Declarations


    @Declarations.target_registry(Declarations.Core)
    class SqlViewBase:
        pass

Query
~~~~~

Overload the SqlAlchemy Query class. Allow to add feature to minify the
source file.

::

    from anyblok import Declarations


    @Declarations.target_registry(Declarations.Core)
    class Query
        pass

Session
~~~~~~~

Over load the SqlAlchemy Session class.

::

    from anyblok import Declarations


    @Declarations.target_registry(Declarations.Core)
    class Session
        pass

Insrumented List
~~~~~~~~~~~~~~~~

::

    from anyblok import Declarations


    @Declarations.target_registry(Declarations.Core)
    class InstrumentedList
        pass

Instrumented List if the class returned by the Query for all the list result
as:

* query.all()
* relationship list (Many2Many, One2Many)

Add some feature as get a specific property of call a method on all the
elements::

    MyModel.query().all().foo(bar)

Share the table between more than one model
-------------------------------------------

SqlAlchemy allow two method to share a table between two or more mappin class:

* Inherit a SQL Model in a non SQL Model::

    @target_registry(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @target_registry(Model)
    class Test2(Model.Test):
        pass

    ----------------------------------------

    t1 = Test1.insert(name='foo')
    assert Test2.query().filter(Test2.id == t1.id,
                                Test2.name == t1.name).count() == 1

* Share the ``__table__``.
    AnyBlok can't give the table at the declaration, because the table doesn't
    exist yet. But during the assembling, if the table exist and le model
    have the name of this table then AnyBlok link directly the table. To
    define the table you must use the named argument tablename in the
    target_registry

    ::

        @target_registry(Model)
        class Test:
            id = Integer(primary_key=True)
            name = String()

        @target_registry(Model, tablename=Model.Test)
        class Test2:
            id = Integer(primary_key=True)
            name = String()

        ----------------------------------------

        t1 = Test1.insert(name='foo')
        assert Test2.query().filter(Test2.id == t1.id,
                                    Test2.name == t1.name).count() == 1

    .. warning::
        They are any check on the existing columns.

Share the view between more than one model
------------------------------------------

Share the view between to Model is the merge between:

* Create a View Model
* Share the same table between more than one model.

.. warning::

    For the view you must redined the column in the Model which take the view
    with Inherit or simple Share by tablename

Specific behariour
------------------

AnyBlok implement some of facility to help the writter of the source file.

Cache
~~~~~

The cache allow to call more than one time a method without have got any
difference in the result. But the cache must also depend of the registry (
database) and the model. The cache of anyblok can be put on a Model, a Core or
a Mixin method. If the cache is on a Core or a Mixin then the usecase depend
of the registry name of the assembled model.

Use ``Declarations.cache`` or ``Declarations.classmethod_cache`` to apply a
cache on method

Cache the method of a Model::

    @target_registry(Model)
    class Foo:

        @classmethod_cache()
        def bar(cls):
            import random
            return random.random()


    -----------------------------------------

    assert Foo.bar() == Foo.bar()


Cache the method coming from a Mixin::

    @target_registry(Mixin)
    class MFoo:

        @classmethod_cache()
        def bar(cls):
            import random
            return random.random()

    @target_registry(Model)
    class Foo(Mixin.MFoo):
        pass

    @target_registry(Model)
    class Foo2(Mixin.MFoo):
        pass


    -----------------------------------------

    assert Foo.bar() == Foo.bar()
    assert Foo2.bar() == Foo2.bar()
    assert Foo.bar() != Foo2.bar()


Cache the method coming from a Mixin::

    @target_registry(Core)
    class Base

        @classmethod_cache()
        def bar(cls):
            import random
            return random.random()

    @target_registry(Model)
    class Foo:
        pass

    @target_registry(Model)
    class Foo2:
        pass


    -----------------------------------------

    assert Foo.bar() == Foo.bar()
    assert Foo2.bar() == Foo2.bar()
    assert Foo.bar() != Foo2.bar()

Event
~~~~~

Simple implementation of synchronious ``event``::


    @target_registry(Model)
    class Event:
        pass

    @target_registry(Model)
    class Test:

            x = 0

            @Declarations.addListener(Model.Event, 'fireevent')
            def my_event(cls, a=1, b=1):
                cls.x = a * b

    ---------------------------------------------

    registry.Event.fire('fireevent', a=2)
    assert registry.Test.x == 2

.. note::

    The decorated method is seen as a classmethod

This api give:

* decorator ``addListener`` which link the decorated method with the event.
* ``fire`` method with the params
    - event: string name of the event
    - \*args: positionnal arguments to pass att the decorated method
    - \*\*kwargs: named argument to pass at the decorated method

It is possible to overload an existing event listner, just by overload the
decorated method::

    @target_registry(Model)
    class Test:

        @classmethod
        def my_event(cls, **kwarg):
            res = super(Test, cls).my_event(**kwargs)
            return res * 2

    ---------------------------------------------

    registry.Event.fire('fireevent', a=2)
    assert registry.Test.x == 4

.. warning::

    the overload doesn't take the ``addListener`` decorator but the
    classmethod decorator, because the method name has already seen as a
    event listener

Hybrid method
~~~~~~~~~~~~~

Facility to create a SqlAlchemy hybrid method. see the page
http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html#module-sqlalchemy.ext.hybrid

AnyBlok allow to define a hybrid_method which can be overload, because the
real sqlalchemy decorator is applied after assembling in the last overload
of the decorated method::

    @target_registry(Model)
    class Test:

        @Declarations.hybrid_method
        def my_hybrid_method(self):
            return ...

Pre commit hook
~~~~~~~~~~~~~~~

It is possible to call specific classmethods just before the commit of the
session::

    @target_registry(Model)
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

Facility to create a sql alias for the sql query by the orm::

    select * from my_table the_table_alias.

This facility is given by SqlAlchemy, and anyblok add this functionnality
directly in the Model::

    BlokAliased = registry.System.Blok.aliased()

.. note:: See the
    http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.aliased
    to known the params of the ``aliased`` method

    .. warning:: The first arg is alredy passed by AnyBlok
