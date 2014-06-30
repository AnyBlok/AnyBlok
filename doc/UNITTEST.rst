Helper for unittest
===================

For unittest classes are available to have some fonctionnality

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


.. warning:: 
    The unit test in the framework cann't be working with other eggs like
    ``anyblok_web_server`` because this blok add new entry declaration and 
    the test are not made to be so flexible
