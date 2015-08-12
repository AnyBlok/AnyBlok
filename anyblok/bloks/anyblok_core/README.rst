.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

This blok is required by all anyblok application. This blok define the main
fonctionnality to install, update and uninstall blok. And also list the
known models, fields, columns and relationships:

* Core ``Model``
    - Base: inherited by all the Model
    - SqlBase: Inherited only by the model with table
    - SqlViewBase: Inherited only by the sql view model

* System Models
    - Blok: List the bloks
    - Model: List the models
    - Field: List of the fields
    - Column: List of the columns
    - Relationship: List of the relation ship
    - Sequence: Define database sequence
    - Parameter: Define application parameter

Sequence
~~~~~~~~

Some behaviours need to have sequence::

    sequence = registry.System.Sequence.insert(
        code="string code",
        formater="One prefix {seq} One suffix")

.. note::

    It is a python formater, you can use the variable:

    * seq: numero of the current data base sequence
    * code: code field
    * id: id field

Get the next value of the sequence::

    sequence.nextval()

exemple::

    seq = Sequence.insert(code='SO', formater="{code}-{seq:06d}")
    seq.nextval()
    >>> SO-000001
    seq.nextval()
    >>> SO-000002

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
