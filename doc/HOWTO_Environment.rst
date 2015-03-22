.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

Environmment
============

Environment stocks contextual variable. by default the environment is stocked
in the current ``Thread``.

Use the current environment
---------------------------

The environment can be used whereever in the code.

Generic use
~~~~~~~~~~~

To get or set variable in environment, you must import the
``EnvironmentManager``::

    from anyblok.environment import EnvironmentManager

Set a variable::

    EnvironmentManager.set('my variable name', OneValue)

Get a variable::

    EnvironmentManager.get('my variable name', default=OneDefaultValue)

Use in a ``Model``
~~~~~~~~~~~~~~~~~~

A facility are add in the ``registry_base``. This class is inherited by all
the model.

Get the environment in ``Model`` method or classmethod::

    self.Env  # or cls.Env

Set a variable::

    self.Env.set('my variable name', OneValue)

Get a variable::

    self.Env.get('my variable name', default=OneDefaultValue)

Define a new environment type
-----------------------------

If you do not want to stock the environment in the ``Thread``, you  must
implement a new type of environment.

This type is a simple class which have theses class methods:

* scoped_function_for_session
* setter
* getter

::

    MyEnvironmentClass:

        @classmethod
        def scoped_function_for_session(cls):
            ...

        @classmethod
        def setter(cls, key, value):
            ...

        @classmethod
        def getter(cls, key, default):
            ...
            return value

Declare your class as the Environment class::

    EnvironmentManager.define_environment_cls(MyEnvironmentClass)


The classmethod ``scoped_function_for_session`` is passed at SQLAlchemy
``scoped_session`` function `see <http://docs.sqlalchemy.org/en/rel_0_9/orm/
contextual.html#contextual-thread-local-sessions>`_
