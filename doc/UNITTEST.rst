.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

Helper for unittest
===================

For unittest, classes are available to offer some fonctionnalities

.. automodule:: anyblok.tests.testcase


TestCase
--------

::

    from anyblok.tests.testcase import TestCase

.. autoclass:: TestCase
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:


DBTestCase
----------

.. warning:: this testcase destroys the test database for each unittest

.. autoclass:: DBTestCase
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:


BlokTestCase
------------

.. autoclass:: BlokTestCase
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex:
