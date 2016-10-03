.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
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

AnyBlok is hosted on `github <http://github.com>`_ - the main project
page is at http://github.com/AnyBlok/AnyBlok or 
http://code.anyblok.org. Source code is tracked here
using `GIT <https://git-scm.com>`_.

Releases and project status are available on Pypi at 
http://pypi.python.org/pypi/anyblok.

The most recent published version of this documentation should be at
http://doc.anyblok.org.

Project Status
--------------

AnyBlok is currently in alpha status and is expected to be fairly
stable.   Users should take care to report bugs and missing features on an as-needed
basis.  It should be expected that the development version may be required
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

.. note:: AnyBlok use Python version >= 3.3

Unit Test
---------

Run the framework test with ``nose``::

    pip install nose
    nosetests anyblok/tests

Run all the installed bloks::

    anyblok_nose -c config.file.cfg

Run the blok tests at the installation::

    anyblok_updatedb -c config.file.cfg --install_bloks myblok --test-blok-at-install

AnyBlok is tested using `Travis <https://travis-ci.org/AnyBlok/AnyBlok>`_

Dependencies
------------

AnyBlok works with **Python 3.3** and later. The install process will 
ensure that `SQLAlchemy <http://www.sqlalchemy.org>`_, 
`Alembic <http://alembic.readthedocs.org/>`_,
`SQLAlchemy-Utils <http://sqlalchemy-utils.readthedocs.org/>`_ are installed, 
in addition to other dependencies.

AnyBlok works with SQLAlchemy from version **1.0.11**,
Alembic from version **0.8.4** and SQLAlchemy-Utils from version **0.31.4**.
The latest version of them is strongly recommended.


Contributing (hackers needed!)
------------------------------

Anyblok is at a very early stage, feel free to fork, talk with core dev, and spread the word!

Author
------

Jean-Sébastien Suzanne

Contributors
------------

`Anybox <http://anybox.fr>`_ team:

* Georges Racinet
* Christophe Combelles
* Jean-Sébastien Suzanne
* Florent Jouatte
* Simon André
* Pierre Verkest

other:

* Sébastien Chazallet
* Franck Bret

Bugs
----

Bugs and feature enhancements to AnyBlok should be reported on the `Issue 
tracker <http://issue.anyblok.org>`_.
