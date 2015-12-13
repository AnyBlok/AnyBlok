.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. note::
    Require the anyblok-io-csv blok

Exporter
~~~~~~~~

Add an exporter mode (CSV) in AnyBlok::

    Exporter = registry.IO.Exporter.CSV

Define what export::

    csv_delimiter = ','
    csv_quotechar = '"'
    model = ``Existing model name``
    fields = [
        {'name': 'field name'},
        {'name': 'fieldname1.fieldname2. ... .fieldnamen}  #  fieldname1, fieldname 2 must be Many2One or have foreign keys
        {'name': 'field', model="external_id"}  # field must be Many2One or foreign_keys or primary keys
        ...
    ]

Create the Exporter::

    exporter = Exporter.insert(csv_delimiter=csv_delimiter,
                               csv_quotechar=csv_quotechar,
                               model=model,
                               fields=fields)

.. warning::

    You can also make insert with registry.IO.Exporter directly

Run the export::

    fp = exporter.run(entries)  # entries are instance of the ``model``

Importer
~~~~~~~~

Add an importer mode (CSV) in AnyBlok::

    Importer = registry.IO.Importer.CSV

Define what import::

    csv_delimiter = ','
    csv_quotechar = '"'
    model = ``Existing model name``
    with open(..., 'rb') as fp:
        file_to_import = fp.read()

Create the Exporter::

    importer = Importer.insert(csv_delimiter=csv_delimiter,
                               csv_quotechar=csv_quotechar,
                               model=model,
                               file_to_import=file_to_import)

.. warning::

    You can also make insert with registry.IO.Importer directly

Run the import::

    res = importer.run()

The result is a dict with:

* error_found: List the error, durring the import
* created_entries: Entries created by the import
* updated_entries: Entries updated by the import

List of the options for the import:

* csv_on_error:
    - raise_now: Raise now
    - raise_at_the_end (default): Raise at the end
    - ignore: Ignore and continue
* csv_if_exist:
    - pass: Pass to the next record
    - overwrite (default): Update the record
    - create: Create another record
    - raise: Raise an exception
* csv_if_does_not_exist:
    - pass: Pass to the next record
    - create (default): Create another record
    - raise: Raise an exception
