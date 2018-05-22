.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

Authorization
~~~~~~~~~~~~~

.. automodule:: anyblok.bloks.anyblok_core.authorization

.. autoanyblok-declaration:: Authorization
    :members:
    :undoc-members:

.. autoclass:: DefaultModelDeclaration
    :members:
    :undoc-members:
    :show-inheritance:

Core Models
~~~~~~~~~~~

.. automodule:: anyblok.bloks.anyblok_core.core.base

.. autoanyblok-declaration:: Base
    :members:

.. automodule:: anyblok.bloks.anyblok_core.core.sqlbase

.. autoclass:: SqlMixin
    :members:

.. autoanyblok-declaration:: SqlBase
    :members:

.. automodule:: anyblok.bloks.anyblok_core.core.sqlviewbase

.. autoanyblok-declaration:: SqlViewBase
    :members:

.. automodule:: anyblok.bloks.anyblok_core.core.instrumentedlist

.. autoanyblok-declaration:: InstrumentedList
    :members:

.. automodule:: anyblok.bloks.anyblok_core.core.query

.. autoanyblok-declaration:: Query
    :members:

.. automodule:: anyblok.bloks.anyblok_core.core.session

.. autoanyblok-declaration:: Session
    :members:

System Models
~~~~~~~~~~~~~

.. automodule:: anyblok.bloks.anyblok_core.system

.. autoanyblok-declaration:: System
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.blok

.. autoanyblok-declaration:: Blok
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.cache

.. autoanyblok-declaration:: Cache
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.field

.. autoanyblok-declaration:: Field
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.column

.. autoanyblok-declaration:: Column
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.relationship

.. autoanyblok-declaration:: RelationShip
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.model

.. autoanyblok-declaration:: Model
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.parameter

.. autoanyblok-declaration:: Parameter
    :members:

.. automodule:: anyblok.bloks.anyblok_core.system.sequence

.. autoanyblok-declaration:: Sequence
    :members:

.. _blok_anyblok_core_documentation:

Documentation Models
~~~~~~~~~~~~~~~~~~~~

.. automodule:: anyblok.bloks.anyblok_core.documentation

.. autoanyblok-declaration:: DocElement
    :members:

.. autoanyblok-declaration:: Documentation
    :members:

.. automodule:: anyblok.bloks.anyblok_core.documentation.blok

.. autoanyblok-declaration:: Blok
    :members:

.. automodule:: anyblok.bloks.anyblok_core.documentation.model

.. autoanyblok-declaration:: Model
    :members:

.. automodule:: anyblok.bloks.anyblok_core.documentation.model.attribute

.. autoanyblok-declaration:: Attribute
    :members:

.. automodule:: anyblok.bloks.anyblok_core.documentation.model.field

.. autoanyblok-declaration:: Field
    :members:

.. _blok_anyblok_core_mixins:

Mixins
~~~~~~

.. automodule:: anyblok.bloks.anyblok_core.mixins

.. autoanyblok-declaration:: ForbidUpdate
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: ForbidDelete
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: ReadOnly
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: ConditionalForbidUpdate
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: ConditionalForbidDelete
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: ConditionalReadOnly
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: BooleanForbidUpdate
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: BooleanForbidDelete
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: BooleanReadOnly
    :members:
    :show-inheritance:

.. autoanyblok-declaration:: StateReadOnly
    :members:
    :show-inheritance:

.. _blok_anyblok_core_exceptions:

Exceptions
~~~~~~~~~~

.. automodule:: anyblok.bloks.anyblok_core.exceptions

.. autoexception:: CoreBaseException
    :members:
    :show-inheritance:

.. autoexception:: SqlBaseException
    :members:
    :show-inheritance:

.. autoexception:: QueryException
    :members:
    :show-inheritance:

.. autoexception:: CacheException
    :members:
    :show-inheritance:

.. autoexception:: ParameterException
    :members:
    :show-inheritance:

.. autoexception:: ForbidUpdateException
    :members:
    :show-inheritance:

.. autoexception:: ForbidDeleteException
    :members:
    :show-inheritance:
