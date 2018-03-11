.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.


Parameter
~~~~~~~~~

Parameter is a simple model key / value:

* key: must be a String
* value: any type

Add new value in the paramter model::

    registry.System.Parameter.set(key, value)

.. note::

    If the key already exist, then the value of the key is updated

Get an existing value::

    registry.System.Parameter.get(key)

.. warning::

    If the key does not existing then an ExceptionParameter will raise

Check the key exist::

    registry.System.Parameter.is_exist(key)  # return a Boolean

Return and remove the parameter::

    registry.System.Parameter.pop(key)
