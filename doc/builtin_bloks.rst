.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

Builtin Bloks
=============

AnyBlok ships with some builtin Bloks. Among them,
:ref:`anyblok-core <blok_anyblok_core>` is essential for the
framework itself, while the others provide optional functionalities
that have been found generic enough that uniformity across
applications would be a good thing.

.. contents:: Covered Bloks
   :local:
   :depth: 1

.. _blok_anyblok_core:

Blok anyblok-core
-----------------

.. automodule:: anyblok.bloks.anyblok_core
.. autoclass:: AnyBlokCore
    :show-inheritance:

    .. autoattribute:: name
    .. autoattribute:: version
    .. autoattribute:: author
    .. autoattribute:: autoinstall
    .. autoattribute:: priority


.. include:: ../anyblok/bloks/anyblok_core/CODE.rst

.. _blok_io:

Blok IO
-------

.. automodule:: anyblok.bloks.io
.. autoclass:: AnyBlokIO
    :members:
    :undoc-members:
    :show-inheritance:

.. include:: ../anyblok/bloks/io/README.rst
.. include:: ../anyblok/bloks/io/CODE.rst

.. _blok_io_csv:

Blok IO CSV
-----------

.. automodule:: anyblok.bloks.io_csv
.. autoclass:: AnyBlokIOCSV
    :members:
    :undoc-members:
    :show-inheritance:

.. include:: ../anyblok/bloks/io_csv/README.rst
.. include:: ../anyblok/bloks/io_csv/CODE.rst

.. _blok_io_xml:

Blok IO XML
-----------

.. automodule:: anyblok.bloks.io_xml
.. autoclass:: AnyBlokIOXML
    :members:
    :undoc-members:
    :show-inheritance:

.. include:: ../anyblok/bloks/io_xml/README.rst
.. include:: ../anyblok/bloks/io_xml/CODE.rst

.. _blok_model_authz:

Blok Model Authz
----------------

.. automodule:: anyblok.bloks.model_authz
.. autoclass:: ModelBasedAuthorizationBlok
    :members:
    :undoc-members:
    :show-inheritance:

.. include:: ../anyblok/bloks/model_authz/README.rst
.. include:: ../anyblok/bloks/model_authz/CODE.rst
