.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. AnyBlok documentation master file, created by
   sphinx-quickstart on Mon Feb 24 10:12:33 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

AnyBlok documentation
=====================

AnyBlok is a Python framework allowing to create highly dynamic and modular
applications on top of SQLAlchemy. Applications are made of "bloks" that can be
installed, extended, replaced, upgraded or uninstalled. Bloks can provide SQL
Models, Column types, Fields, Mixins, SQL views, or plain Python code unrelated
to the database.  Models can be dynamically customized, modified, or extended
without strong dependencies between them, just by adding new bloks. Bloks are
declared using `setuptools` entry-points.

AnyBlok is released under the terms of the `Mozilla Public License`.

.. toctree::
    :maxdepth: 2

    FRONT.rst
    HOWTO_CREATE_APP.rst
    HOWTO_ADD_ENTRY_OR_CORE_TYPE.rst
    HOWTO_Environment.rst
    MEMENTO.rst
    CODE.rst
    UNITTEST.rst
    BLOKS.rst
    CHANGES.rst
    ROADMAP.rst
    LICENSE.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

