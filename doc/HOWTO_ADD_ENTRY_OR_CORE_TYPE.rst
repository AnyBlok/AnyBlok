.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

How to add a new ``Type`` /core
===============================

``Type`` and ``Core`` are both ``Declarations``.

Difference between ``Core`` and ``Type``
----------------------------------------

``Core`` is also an Entry ``Type``. But it is a particular entry ``Type``.
``Core`` is used to define low level at the entry ``Type``. For example
the ``Core.Base`` is the low level at all the ``Model``. Modify the behaviours
of the ``Core.Base`` is equal to modify the behaviours of all the ``Model``.

this is the inheritance model of the ``Model`` ``Type``

+--------------------+------------------------------------+-------------------+
| ``Entry`` ``Type`` |    inheritance ``Types``           |      Core         |
+====================+====================================+===================+
|      Model         |          Model     /   Mixin       |        Base       |
+--------------------+------------------------------------+-------------------+

Declare a new ``Type``
----------------------

The declaration of new ``Type``, is declarations of a new type of declaration.
The known ``Type`` declarations are:

* Model
* Mixin
* Core
* AuthorizationPolicyAssociation

This is an example to declare new entry ``Type``::

    from anyblok import Declarations


    @Declarations.add_declaration_type()
    class MyType:

        @classmethod
        def register(cls, parent, name, cls_, **kwargs):
            ...

        @classmethod
        def unregister(cls, child, cls_):
            ...

The Type must implement:

+---------------------+-------------------------------------------------------+
| Method name         | Description                                           |
+=====================+=======================================================+
|  register           | This ``classmethod`` describe what append when a      |
|                     | a declaration is done by he decorator                 |
|                     | ``Declarations.register``                             |
+---------------------+-------------------------------------------------------+
|  unregister         | This ``classmethod`` describe what append when an     |
|                     | undeclaration is done.                                |
+---------------------+-------------------------------------------------------+

The ``add_declaration_type`` can define the arguments:

+---------------------+-------------------------------------------------------+
| Argument's name     | Description                                           |
+=====================+=======================================================+
| isAnEntry           | **Boolean**                                           |
|                     | Define if the new ``Type`` is an entry, depend of the |
|                     | installation or not of the bloks                      |
+---------------------+-------------------------------------------------------+
| assemble            | **Only for the entry ``Type``**                       |
|                     | Waiting the name of the classmethod which make the    |
|                     | action to group and create a new class with the       |
|                     | complete inheritance tree::                           |
|                     |                                                       |
|                     |     @add_declaration_type(isAnEntry=True,             |
|                     |                           assemble='assemble')        |
|                     |     class MyTpe:                                      |
|                     |         ...                                           |
|                     |                                                       |
|                     |         @classmethod                                  |
|                     |         def assemble(cls, registry):                  |
|                     |             ...                                       |
|                     |                                                       |
|                     | .. warning::                                          |
|                     |     registry is the registry of the database          |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| initialize          | **Only for the entry ``Type``**                       |
|                     | Waiting the name of the classmethod which make the    |
|                     | action to initialize the registry::                   |
|                     |                                                       |
|                     |     @add_declaration_type(isAnEntry=True,             |
|                     |                           initialize='initialize')    |
|                     |     class MyTpe:                                      |
|                     |         ...                                           |
|                     |                                                       |
|                     |         @classmethod                                  |
|                     |         def initialize(cls, registry):                |
|                     |             ...                                       |
|                     |                                                       |
|                     | .. warning::                                          |
|                     |     registry is the registry of the database          |
|                     |                                                       |
+---------------------+-------------------------------------------------------+


Declare a Mixin entry type
--------------------------

``Mixin`` is a ``Type`` to add behaviours, it is not a particular ``Type``.
But it is always very interresting to use it.

AnyBlok had already a ``Mixin`` ``Type`` for the ``Model`` ``Type``. The
``Mixin`` ``Type`` must not be the same for all the entry ``Type``, then
``Model`` inherit only other ``Model`` or ``Declarations.Mixin``. If you add
an another ``Declarations.AnotherMixin`` then ``Model`` won't inherit this
``Mixin`` ``Type``.

The new ``Mixin`` ``Type`` is easy to add::

    from anyblok import Declarations
    from anyblok.mixin import MixinType


    @Declarations.add_declaration_type(isAnEntry=True)
    class MyMixin(MixinType):
        pass

Declare a new ``Core``
----------------------


The definition of a Core and the Declaration is in different parts

Declarations of a new ``Core``::

    from anyblok.registry import RegistryManager


    RegistryManager.declare_core('MyCore')

Definition or register of an overload of the ``Core`` declaration::

    from anyblok import Declarations


    @Declarations.register(Declarations.Core)
    class MyCore:
        ...

The declaration must be done in the application, not in the blok. The
is only done in the blok.

.. warning::

    ``Core`` can't inherit ``Model``, ``Mixin`` or other Type
