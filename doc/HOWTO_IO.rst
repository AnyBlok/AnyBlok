.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

IO
==

.. note::

    Require tha the anyblok-io is installed

TODO

Mapping
-------

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
