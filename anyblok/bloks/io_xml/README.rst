.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. note::
    Require the anyblok-io-xml blok

Exporter
~~~~~~~~

TODO

Importer
~~~~~~~~

Add an importer mode (XML) in AnyBlok::

    Importer = registry.IO.Importer.XML

Define what import::

    model = ``Existing model name``
    with open(..., 'rb') as fp:
        file_to_import = fp.read()

Create the Exporter::

    importer = Importer.insert(model=model,
                               file_to_import=file_to_import)

.. warning::

    You can also make insert with registry.IO.Importer directly

Run the import::

    res = importer.run()

The result is a dict with:

* error_found: List the error, durring the import
* created_entries: Entries created by the import
* updated_entries: Entries updated by the import

Root structure of the XML file::

    <records on_error="...">
        ...
    </records>

raise can have the value:

* raise (dafault)
* ignore

records node can have:

* commit: commit the import, only if no error found
* record: import one record

Add a record::

    <records>
        <record>
            ...
            <field name="..." />
            ...
        </record>
    </records>

Record attribute:

* model: if not filled, then the importer will indicate the model
* external_id: Mapping key
* param: Mapping key only for the import (not save)
* on_error:
    - raise
    - ignore (default)
* if_exist:
    - overwrite (default)
    - create
    - pass: continue to the next record
    - continue: continue on the sub record without take this record
    - raise
* id_does_not_exist:
    - create (default)
    - pass
    - raise

The field node represente a Field, a Column or RelationShip, the attribute are:

* name (required): name of the field, column or relation ship

Case of the relation ship, they have some more attribute:

* external_id:
* param:
* on_error:
    - raise
    - ignore (default)
* if_exist:
    - overwrite (default)
    - create
    - pass: continue to the next record
    - continue: continue on the sub record without take this record
    - raise
* id_does_not_exist:
    - create (default)
    - pass
    - raise

Many2One and One2One declaration is directly in the field node::

    <records
        <record
            ...
            <field name="Many2One or One2One">
                ...
                <field name="..." />
                ...
            </field>
            ...
        </record>
    </records>

One2Many and Many2Many declarations is also in the field but with a record
node::

    <records
        <record
            ...
            <field name="Many2Many or One2Many">
                ...
                <record>
                    ...
                    <field name="..." />
                    ...
                </record>
                ...
            </field>
            ...
        </record>
    </records>
