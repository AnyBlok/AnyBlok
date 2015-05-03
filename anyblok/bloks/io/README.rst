.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. note::

    Require the anyblok-io blok

Mapping
~~~~~~~

``Model.IO.Mapping`` allows to link a ``Model`` instance by a ``Model``
namesapce and str key. this key is an external *ID*

Save an instance with a key::

    Blok = self.registry.System.Blok
    blok = Blok.query().filter(Blok.name == 'anyblok-core').first()
    self.registry.IO.Mapping.set('External ID', blok)

.. warning::

    By default if you save another instance with the same key and the same
    model, an ``IOMapingSetException`` will be raised. Il really you want
    this mapping you must call the set method with the named argument
    **raiseifexist=False**::

        self.registry.IO.Mapping.set('External ID', blok, raiseifexist=False)


Get an entry in the mapping::

    blok2 = self.registry.IO.Mapping.get('Model.System.Blok', 'External ID')
    assert blok2 is blok

Formater
~~~~~~~~

The goal of the formater is to get:

* value from string
* value from mapping key
* string from value
* mapping key from value

The value is the value of the field.

.. warning::

    The relation ships are particulare cases. The value is the json of the
    primary keys. The Many2Many and the One2Many are the json of the list of
    the primary keys

Exporter
~~~~~~~~

The ``Model.IO.Exporter`` export some entries in fonction of configuration.
``anyblok-io`` blok doesn't give complete exporter, just the base Model
to standardize all the possible export::

    exporter = registry.IO.Exporter.insert(...)  # create a exporter
    entries = ...  # entries are instance of model
    fp = exporter.run(entries)
    # fp is un handler on the opened file (StringIO)

Importer
~~~~~~~~

The ``Model.IO.Importer`` import some entries in fonction of configuration.
``anyblok-io`` blok doesn't give complete importer, just the base Model
to standardize all the possible import::

    importer = registry.IO.Importer.insert(...)  # create an importer
    # the file to import are filled in the parameter
    entries = importer.run()
