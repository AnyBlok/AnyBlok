.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. AnyBlok documentation master file, created by
   sphinx-quickstart on Mon Feb 24 10:12:33 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Front Matter
============

Information about the AnyBlok project.

Project Homepage
----------------

AnyBlok is hosted on `Bitbucket <http://bitbucket.org>`_ - the main project
page is at https://bitbucket.org/jssuzanne/anyblok. Source code is tracked here
using `Mercurial <http://mercurial.selenic.com>`_.

.. Releases and project status are available on Pypi at
.. http://pypi.python.org/pypi/anyblok.

The most recent published version of this documentation should be at
http://docs.anybox.fr/anyblok/default.

.. This version of the documentation is for the release 0.1.0
.. at http://docs.anybox.fr/anyblok/0.1.0.

Project Status
--------------

AnyBlok is currently in beta status and is expected to be fairly
stable.   Users should take care to report bugs and missing features on an as-needed
basis.  It should be expected that the development version may be required
for proper implementation of recently repaired issues in between releases;
the latest master is always available at https://bitbucket.org/jssuzanne/anyblok/get/default.tar.gz.
or https://bitbucket.org/jssuzanne/anyblok/get/default.zip

Installation
------------

.. Install released versions of AnyBlok from the Python package index with 
.. `pip <http://pypi.python.org/pypi/pip>`_ or a similar tool::

..    pip install anyblok

Installation via source distribution is via the ``setup.py`` script::

    python setup.py install

Installation will add the ``anyblok`` commands to the environment.

Dependencies
------------

AnyBlok works with **Python 3.2** and later. The install process will 
ensure that `SQLAlchemy <http://www.sqlalchemy.org>`_, 
`Alembic <http://alembic.readthedocs.org/>`_ are installed, in addition to 
other dependencies.  AnyBlok will work with SQLAlchemy as of version **0.9.8**. 
AnyBlok will work with Alembic as of version **0.7.3**.
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
.. * Sandrine Chaufournais
* Jean-Sébastien Suzanne
* Florent Jouatte
* Simon André
* Clovis Nzouendjou
* Pierre Verkest
* Franck Bret

Bugs
----

Bugs and feature enhancements to AnyBlok should be reported on the `Bitbucket
issue tracker <https://bitbucket.org/jssuzanne/anyblok/issues?status=new&status=open>`_.
