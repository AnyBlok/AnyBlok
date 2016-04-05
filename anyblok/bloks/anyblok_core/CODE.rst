.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

API doc
~~~~~~~

**Authorization**

.. automodule:: anyblok.bloks.anyblok_core.authorization

.. autoclass:: Authorization                                                     
    :members:                                                                   
    :undoc-members:                                                             
    :show-inheritance:
    :noindex:

.. autoclass:: DefaultModelDeclaration                                                     
    :members:                                                                   
    :undoc-members:                                                             
    :show-inheritance:
    :noindex:

**Core**

.. automodule:: anyblok.bloks.anyblok_core.core.base

.. autoanyblok-declaration:: Base                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.core.sqlbase

.. autoclass:: SqlMixin                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoanyblok-declaration:: SqlBase                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.core.sqlviewbase

.. autoanyblok-declaration:: SqlViewBase                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.core.instrumentedlist

.. autoanyblok-declaration:: InstrumentedList                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.core.query

.. autoanyblok-declaration:: Query                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.core.session

.. autoanyblok-declaration:: Session                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

**system**

.. automodule:: anyblok.bloks.anyblok_core.system

.. autoanyblok-declaration:: System                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.blok

.. autoanyblok-declaration:: Blok                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.cache

.. autoanyblok-declaration:: Cache                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.field

.. autoanyblok-declaration:: Field                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.column

.. autoanyblok-declaration:: Column                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.relationship

.. autoanyblok-declaration:: RelationShip                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.cron

.. autoanyblok-declaration:: Cron                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoanyblok-declaration:: Job                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoanyblok-declaration:: Worker                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.model

.. autoanyblok-declaration:: Model                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.parameter

.. autoanyblok-declaration:: Parameter                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.system.sequence

.. autoanyblok-declaration:: Sequence                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

**documentation**

.. automodule:: anyblok.bloks.anyblok_core.documentation

.. autoanyblok-declaration:: DocElement                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoanyblok-declaration:: Documentation                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.documentation.blok

.. autoanyblok-declaration:: Blok                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.documentation.model

.. autoanyblok-declaration:: Model                                                     
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.documentation.model.attribute

.. autoanyblok-declaration:: Attribute 
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. automodule:: anyblok.bloks.anyblok_core.documentation.model.field

.. autoanyblok-declaration:: Field
    :members:                                                                   
    :show-inheritance:
    :noindex:

**exception**

.. automodule:: anyblok.bloks.anyblok_core.exceptions

.. autoexception:: CoreBaseException
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoexception:: SqlBaseException
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoexception:: QueryException
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoexception:: CacheException
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoexception:: ParameterException
    :members:                                                                   
    :show-inheritance:
    :noindex:

.. autoexception:: CronWorkerException
    :members:                                                                   
    :show-inheritance:
    :noindex:
