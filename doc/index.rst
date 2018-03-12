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
applications on top of the SQLAlchemy ORM. Applications are made of
"bloks" that can be installed, extended, replaced, upgraded or uninstalled.

Bloks can provide SQL Models, Column types, Fields, Mixins, SQL views,
or even plain Python code unrelated to the database, and all of these
can be dynamically customized, modified, or extended
without strong dependencies between them, just by adding new bloks.

Bloks are declared (made available) through dedicated setuptools entry
points, and are explicitely *installed* in the
database, which provides the needed dynamicity for multi-tenant
scenarios: a given AnyBlok process can connect to several databases,
and execute different sets of code on each of them, according
to their installed bloks. Installing bloks could, e.g., be done through
some HTTP interface (not provided by AnyBlok itself).

That being said, Anyblok's scope of usage is by no means limited to
multi-tenant applications. The flexibility and extendability it
provides can be enjoyed even when working on a single database.

AnyBlok is released under the terms of the :doc:`Mozilla Public
License version 2 <LICENSE>`.

.. toctree::
    :maxdepth: 2

    FRONT.rst
    basic_usage
    advanced_topics
    MEMENTO.rst
    internals
    builtin_bloks
    CHANGES.rst
    ROADMAP.rst
    LICENSE.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

