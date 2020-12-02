.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..    Copyright (C) 2019 Hugo QUEZADA <gohu@hq.netlib.re>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. AnyBlok documentation master file, created by
   sphinx-quickstart on Mon Feb 24 10:12:33 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. contents::

Front Matter
============

Information about the AnyBlok project.

Project Homepage
----------------

AnyBlok is a Python framework allowing to create highly dynamic and modular
applications on top of SQLAlchemy.

AnyBlok is released under the terms of the `Mozilla Public License`.

AnyBlok is hosted on `github <https://github.com>`_ - the main project
page is at https://github.com/anyblok/anyblok or
http://code.anyblok.org. source code is tracked here
using `git <https://git-scm.com>`_.

Releases and project status are available on Pypi at
https://pypi.python.org/pypi/anyblok.

The most recent published version of the documentation should be at
https://doc.anyblok.org.

There is a tutorial to teach you how to develop applications with AnyBlok at
https://anyblok.gitbooks.io/anyblok-book/content/en/

Project Status
--------------

AnyBlok is expected to be stable.
Some early partners are using it on production and are involved in
the project development.
We are aiming to make a stable release as soon as possible.

Users should take care to report bugs and missing features on an as-needed
basis.

It should be expected that the development version may be required
for proper implementation of recently repaired issues in between releases;
the latest master is always available at https://github.com/AnyBlok/AnyBlok/archive/master.zip.

Installation
------------

Install released versions of AnyBlok from the Python package index with 
`pip <http://pypi.python.org/pypi/pip>`_ or a similar tool::

    pip install anyblok

Installation via source distribution is via the ``setup.py`` script::

    python setup.py install

Installation will add the ``anyblok`` commands to the environment.

.. note:: AnyBlok use Python version >= 3.6

Running Tests
-------------

.. .. seealso:: the :ref:`section about testing of AnyBlok applications
..              <basedoc_tests>`.


To run framework tests with ``pytest``::

    pip install pytest
    ANYBLOK_DATABASE_DRIVER postgresql ANYBLOK_DATABASE_NAME test_anyblok py.test anyblok/tests

To run tests of all installed bloks::

    anyblok_createdb --db-name test_anyblok --db-driver-name postgresql --install-all-bloks
    ANYBLOK_DATABASE_DRIVER postgresql ANYBLOK_DATABASE_NAME test_anyblok py.test anyblok/bloks

AnyBlok is tested continuously using `Travis CI
<https://travis-ci.org/AnyBlok/AnyBlok>`_

Contributing (hackers needed!)
------------------------------

AnyBlok is ready for production usage even though it can be
improved and enriched.
Feel free to fork, talk with core dev, and spread the word !

Author
------

Jean-Sébastien Suzanne

Contributors
------------

* Jean-Sébastien Suzanne
* Georges Racinet
* Pierre Verkest
* Franck Bret
* Denis Viviès
* Alexis Tourneux
* Hugo Quezada
* Simon André
* Florent Jouatte
* Christophe Combelles
* Sébastien Chazallet

Bugs
----

Bugs and feature enhancements to AnyBlok should be reported on the `Issue 
tracker <http://issue.anyblok.org>`_.
