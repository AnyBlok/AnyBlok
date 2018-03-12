.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

Basic usage
===========

To demonstrate, we will write a simple application; let's call it
``WorkApp``.

Here are the Models we'll create, with their fields.
Anyblok being an ORM framework, these will be Python classes, backed
by database tables.


* Employee
    - name: employee's name
    - office (Room): the room where the employee works
    - position: employee position (manager, developer...)
* Room
    - number: describe the room in the building
    - address: postal address
    - employees: men and women working in that room
* Address
    - street
    - zipcode
    - city
    - rooms: room list
* Position
    - name: position name

.. _basedoc_bloks:

Bloks
-----
Within AnyBlok, all business logic objects, among them in the first place
:ref:`Models <basedoc_models>` must be declared as part of some Blok.

Bloks themselves are subclasses of the :class:`Blok <anyblok.blok.Blok>`
base class. They have basic metadata attributes (author, version, dependencies…) and
methods to import the business logic objects declarations.

Bloks also bear the methods for installation, update and removal.

Here's a very minimal (and pretty much useless) valid Blok::

    from anyblok.blok import Blok

    class MyFirstBlok(Blok):
        """ This is valid blok """

To demonstrate the extreme modularity that can be achieved with
Anyblok, we'll organize the application in four different bloks:

**Office blok**

File tree::

  workapp
  ├── (...)
  └── office_blok
    ├── __init__.py
    └── office.py

``__init__.py`` file::

    from anyblok.blok import Blok


    class OfficeBlok(Blok):

        version = '1.0.0'
        author = 'Suzanne Jean-Sébastien'
        logo = 'relative/path'

        def install(self):
            """ method called at blok installation time """
            address = self.registry.Address.insert(street='14-16 rue Soleillet',
                                                   zip='75020', city='Paris')
            self.registry.Room.insert(number=308, address=address)

        def update(self, latest_version):
            if latest_version is None:
                self.install()

        @classmethod
        def import_declaration_module(cls):
            from . import office

So for instance, in this example, we'll import the ``office`` module
(which defines ``Address`` and ``Room`` Models, :ref:`see below <basedoc_models>`) and at the time of
first installation (detected by ``latest_version`` being ``None``),
we'll create an ``Address`` and a ``Room`` instance right away, as
base data.

.. note:: this anticipates a bit on the :ref:`Model <basedoc_models>`
          base usage.

**Position blok**

File tree::

  workapp
  ├── (...)
  └── position_blok
      ├── __init__.py
      └── position.py

``__init__.py`` file::

    from anyblok.blok import Blok


    class PositionBlok(Blok):

        version = '1.0.0'

        def install(self):
            self.registry.Position.multi_insert({'name': 'CTO'},
                                                {'name': 'CEO'},
                                                {'name': 'Administrative Manager'},
                                                {'name': 'Project Manager'},
                                                {'name': 'Developer'})

        def update(self, latest_version):
            if latest_version is None:
                self.install()

        @classmethod
        def import_declaration_module(cls):
            from . import position  # noqa


Same here, the installation automatically creates some data, in this
case ``Position`` instances.

**Employee blok**

Bloks can have requirements. Each blok define its dependencies:

* required:
    list of the bloks that must be installed (and loaded at
    startup) before
* optional:
    list of bloks that will be installed before the present
    one, if they are available in the application.

File tree::

    employee_blok
    ├── __init__.py
    ├── config.py
    └── employee.py

``__init__.py`` file::

    from anyblok.blok import Blok


    class EmployeeBlok(Blok):

        version = '1.0.0'

        required = ['office']

        optional = ['position']

        def install(self):
            room = self.registry.Room.query().filter(
                self.registry.Room.number == 308).first()
            employees = [dict(name=employee, room=room)
                         for employee in ('Georges Racinet',
                                          'Christophe Combelles',
                                          'Sandrine Chaufournais',
                                          'Pierre Verkest',
                                          'Franck Bret',
                                          "Simon André",
                                          'Florent Jouatte',
                                          'Clovis Nzouendjou',
                                          "Jean-Sébastien Suzanne")]
            self.registry.Employee.multi_insert(*employees)

        def update(self, latest_version):
            if latest_version is None:
                self.install()

        @classmethod
        def import_declaration_module(cls):
            from . import config
            from . import employee


**EmployeePosition blok**:

Some bloks can be installed automatically if some specific other bloks are
installed. They are called conditional bloks.

File tree::

    employee_position_blok
    ├── __init__.py
    └── employee.py

``__init__.py`` file::

    from anyblok.blok import Blok

    class EmployeePositionBlok(Blok):

        version = '1.0.0'
        priority = 200

        conditional = [
            'employee',
            'position',
        ]

        def install(self):
            Employee = self.registry.Employee

            position_by_employee = {
                'Georges Racinet': 'CTO',
                'Christophe Combelles': 'CEO',
                'Sandrine Chaufournais': u"Administrative Manager",
                'Pierre Verkest': 'Project Manager',
                'Franck Bret': 'Project Manager',
                u"Simon André": 'Developer',
                'Florent Jouatte': 'Developer',
                'Clovis Nzouendjou': 'Developer',
                u"Jean-Sébastien Suzanne": 'Developer',
            }

            for employee, position in position_by_employee.items():
                Employee.query().filter(Employee.name == employee).update({
                    'position_name': position})

        def update(self, latest_version):
            if latest_version is None:
                self.install()

        @classmethod
        def import_declaration_module(cls):
            from . import employee  # noqa

.. warning::
    There are no strong dependencies between conditional blok and bloks,
    so the priority number of the conditional blok must be bigger than bloks
    defined in the `conditional` list. Bloks are loaded by dependencies
    and priorities so a blok with small dependency/priority will be loaded before a blok with
    an higher dependency/priority.

.. _declare_blok:

Bloks registration
------------------

Now that we have our Bloks, they must be registered through the ``bloks`` setuptools `entry point
<https://setuptools.readthedocs.io/en/latest/setuptools.html#entry-points>`_::

    setup(
        # (...)
        entry_points={
            'bloks': [
                'office=workapp.office_blok:OfficeBlok',
                'employee=workapp.employee_blok:EmployeeBlok',
                'position=workapp.position_blok:PositionBlok',
                'employee-position=workapp.employee_position_blok:EmployeePositionBlok',
            ],
        },
    )


.. _basedoc_models:

Models
------
With AnyBlok, most of the business logic is organized as Models.
There are two types of Model:

* SQL: They bear Fields, and correspond to a table in the database,
  that's automatically created and updated if needed.
* Non SQL: No persistent data, but still useful to attach methods onto
  them, which then could be overridden by downstream Bloks.

To declare a Model, use the ``Declarations.register`` decorator::

    from anyblok import Declarations

    @Declarations.register(Declarations.Model)
    class AAnyBlokModel:
        """ The first Model of our application """

.. note:: At this point, it is important to realize that this Model
          class won't be used directly in this form, which is but a
          Declaration. It will actually be just one element of
          a whole inheritance hierarchy, which AnyBlok constructs for each
          database, according to its installed Bloks. This is the fundamental
          way AnyBlok's flexibility works (see :ref:`basedoc_override`).

Here's an example SQL model, with just one Column::

    from anyblok import Declarations
    from anyblok.column import String

    register = Declarations.register
    Model = Declarations.Model


    @register(Model)
    class ASQLModel:

        acolumn = String(label="The first column", primary_key=True)

This Model will be backed by the ``asqlmodel`` table, whose rows will
correspond to Model instances.

Once the application has started, the fully assembled Model class is
available within the Registry, which itself can be accessed in various ways, depending
on the context.

In particular, the Registry is available on any Model
instance as the ``registry`` attribute. So, from instance, from a method of another
Model, we could create an instance of ``ASQLModel`` in this way::

  def mymethod(self):
      self.registry.ASQLModel.insert(acolumn="Foo")

Another example would be the ``install()`` methods of our
:ref:`basedoc_bloks` above.

.. note:: There is a Registry instance for each database, and it holds for each
          Model the resulting concrete class after all overrides
          have been applied.

.. warning::
    SQL Models must have a primary key made of one or more columns
    (those flagged with ``primary_key=True``)

.. note::
    The table name depends on the registry tree. Here the table is ``asqlmodel``.
    If a new model is defined under ASQLModel (example UnderModel:
    ``asqlcolumn_undermodel``), the registry model will be stored
    as Model.ASQLModel.UnderModel

Let's then proceed with our more concrete example:

**office_blok.office**::

    from anyblok import Declarations
    from anyblok.column import Integer, String
    from anyblok.relationship import Many2One

    register = Declarations.register
    Model = Declarations.Model


    @register(Model)
    class Address:

        id = Integer(label="Identifier", primary_key=True)
        street = String(label="Street", nullable=False)
        zip = String(label="Zip", nullable=False)
        city = String(label="City", nullable=False)

        def __str__(self):
            return "%s %s %s" % (self.street, self.zip, self.city)


    @register(Model)
    class Room:

        id = Integer(label="Identifier", primary_key=True)
        number = Integer(label="Number of the room", nullable=False)
        address = Many2One(label="Address", model=Model.Address, nullable=False,
                           one2many="rooms")

        def __str__(self):
            return "Room %d at %s" % (self.number, self.address)

The relationships can also define the opposite relation. Here the ``address`` Many2One relation
also declares the ``room`` One2Many relation on the Address Model.

A Many2One or One2One relationship must have an existing column.
The ``column_name`` attribute allows to choose the linked column, if this
attribute is missing then the value is "'model.table'.'remote_column'"
If the linked column does not exist, the relationship creates the
column with the same type as the remote_column.

**position_blok.position**::

    from anyblok import Declarations
    from anyblok.column import String

    register = Declarations.register
    Model = Declarations.Model


    @register(Model)
    class Position:

        name = String(label="Position", primary_key=True)

        def __str__(self):
            return self.name

**employee_blok.employee**::

    from anyblok import Declarations
    from anyblok.column import String
    from anyblok.relationship import Many2One

    register = Declarations.register
    Model = Declarations.Model


    @register(Model)
    class Employee:

        name = String(label="Number of the room", primary_key=True)
        room = Many2One(label="Office", model=Model.Room, one2many="employees")

        def __str__(self):
            return "%s in %s" % (self.name, self.room)

.. _basedoc_override:

Overriding Models
-----------------

If one declares two Models with the same name, the
second Model will subclass the first one in the final assembled Model
class. This is mostly interesting when the two
declarations belong to different bloks.

**employee_position_blok.employee**::

    from anyblok import Declarations
    from anyblok.relationship import Many2One

    register = Declarations.register
    Model = Declarations.Model


    @register(Model)
    class Employee:

        position = Many2One(label="Position", model=Model.Position, nullable=False)

        def __str__(self):
            res = super(Employee, self).__str__()
            return "%s (%s)" % (res, self.position)

Standalone executables
----------------------

If the AnyBlok application is an HTTP server running through some WSGI compatibility
layer, such as AnyBlok / Pyramid, one does not need to care about
running processes: the WSGI server provides them already.

But in other cases, including background processing alongside HTTP
workers, we need to setup executables.

Add entries in the argparse configuration
+++++++++++++++++++++++++++++++++++++++++

Some applications may require options. Options are grouped by
category. And the application chooses the option category to display.

**employee_blok.config**::

    from anyblok.config import Configuration


    @Configuration.add('message', label="This is the group message")
    def add_interpreter(parser, configuration):
        parser.add_argument('--message-before', dest='message_before')
        parser.add_argument('--message-after', dest='message_after')


Create the executable
+++++++++++++++++++++

The application can be a simple script or a setuptools script. For a setuptools
script, add this in the ``setup.py``::

    setup(
        ...
        entry_points={
            'console_scripts': ['exampleblok=exampleblok.scripts:exampleblok'],
            'bloks': bloks,
        },
    )

The script must display:

* the provided ``message_before``
* the lists of the employee by address and by room
* the provided ``message_after``

**scripts.py**::

    import anyblok
    from logging import getLogger
    from anyblok.config import Configuration

    logger = getLogger()


    def exampleblok():
        # Initialise the application, with a name and a version number
        # select the groupe of options to display
        # return a registry if the database are selected
        registry = anyblok.start(
            'Example Blok', argparse_groups=['message', 'logging'])

        if not registry:
            return

        message_before = Configuration.get('message_before')
        message_after = Configuration.get('message_after')

        if message_before:
            logger.info(message_before)

        for address in registry.Address.query().all():
            for room in address.rooms:
                for employee in room.employees:
                    logger.info(employee)

        if message_after:
            logger.info(message_after)


**Display the help of your application**::

    jssuzanne:anyblok jssuzanne$ ./bin/exampleblok -h
    usage: exampleblok [-h]
                       [--logging-level {NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                       [--logging-level-qualnames LOGGING_LEVEL_QUALNAMES [LOGGING_LEVEL_QUALNAMES ...]]
                       [--logging-config-file LOGGING_CONFIGFILE]
                       [--logging-json-config-file JSON_LOGGING_CONFIGFILE]
                       [--logging-yaml-config-file YAML_LOGGING_CONFIGFILE]
                       [-c CONFIGFILE] [--without-auto-migration]
                       [--db-name DB_NAME] [--db-driver-name DB_DRIVER_NAME]
                       [--db-user-name DB_USER_NAME] [--db-password DB_PASSWORD]
                       [--db-host DB_HOST] [--db-port DB_PORT] [--db-echo]

    [options] -- other arguments

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIGFILE         Relative path of the config file
      --without-auto-migration

    Logging:
      --logging-level {NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL}
      --logging-level-qualnames LOGGING_LEVEL_QUALNAMES [LOGGING_LEVEL_QUALNAMES ...]
                            Limit the log level on a qualnames list
      --logging-config-file LOGGING_CONFIGFILE
                            Relative path of the logging config file
      --logging-json-config-file JSON_LOGGING_CONFIGFILE
                            Relative path of the logging config file (json). Only
                            if the logging config file doesn't filled
      --logging-yaml-config-file YAML_LOGGING_CONFIGFILE
                            Relative path of the logging config file (yaml). Only
                            if the logging and json config file doesn't filled

    Database:
      --db-name DB_NAME     Name of the database
      --db-driver-name DB_DRIVER_NAME
                            the name of the database backend. This name will
                            correspond to a module in sqlalchemy/databases or a
                            third party plug-in
      --db-user-name DB_USER_NAME
                            The user name
      --db-password DB_PASSWORD
                            database password
      --db-host DB_HOST     The name of the host
      --db-port DB_PORT     The port number
      --db-echo

**Create an empty database and call the script**::

    jssuzanne:anyblok jssuzanne$ createdb anyblok
    jssuzanne:anyblok jssuzanne$ ./bin/exampleblok -c anyblok.cfg --message-before "Get the employee ..." --message-after "End ..."
    2014-1129 10:54:27 INFO - anyblok:root - Registry.load
    2014-1129 10:54:27 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-1129 10:54:27 INFO - anyblok:anyblok.registry - Assemble 'Model' entry
    2014-1129 10:54:27 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-1129 10:54:27 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-1129 10:54:27 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'system_cache_id_seq' as owned by integer column 'system_cache(id)', assuming SERIAL and omitting
    2014-1129 10:54:27 INFO - anyblok:anyblok.registry - Initialize 'Model' entry
    2014-1129 10:54:27 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Install the blok 'anyblok-core'
    2014-1129 10:54:27 INFO - anyblok:root - Registry.reload
    2014-1129 10:54:27 INFO - anyblok:root - Registry.load
    2014-1129 10:54:27 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-1129 10:54:27 INFO - anyblok:anyblok.registry - Blok 'office' loaded
    2014-1129 10:54:27 INFO - anyblok:anyblok.registry - Assemble 'Model' entry
    2014-1129 10:54:27 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-1129 10:54:27 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-1129 10:54:27 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'address_id_seq' as owned by integer column 'address(id)', assuming SERIAL and omitting
    2014-1129 10:54:27 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'system_cache_id_seq' as owned by integer column 'system_cache(id)', assuming SERIAL and omitting
    2014-1129 10:54:27 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'room_id_seq' as owned by integer column 'room(id)', assuming SERIAL and omitting
    2014-1129 10:54:27 INFO - anyblok:anyblok.registry - Initialize 'Model' entry
    2014-1129 10:54:28 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Install the blok 'office'
    2014-1129 10:54:28 INFO - anyblok:root - Registry.reload
    2014-1129 10:54:28 INFO - anyblok:root - Registry.load
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Blok 'office' loaded
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Assemble 'Model' entry
    2014-1129 10:54:28 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-1129 10:54:28 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-1129 10:54:28 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'address_id_seq' as owned by integer column 'address(id)', assuming SERIAL and omitting
    2014-1129 10:54:28 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'system_cache_id_seq' as owned by integer column 'system_cache(id)', assuming SERIAL and omitting
    2014-1129 10:54:28 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'room_id_seq' as owned by integer column 'room(id)', assuming SERIAL and omitting
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Initialize 'Model' entry
    2014-1129 10:54:28 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Install the blok 'position'
    2014-1129 10:54:28 INFO - anyblok:root - Registry.reload
    2014-1129 10:54:28 INFO - anyblok:root - Registry.load
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Blok 'office' loaded
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Blok 'employee' loaded
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Assemble 'Model' entry
    2014-1129 10:54:28 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-1129 10:54:28 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-1129 10:54:28 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'system_cache_id_seq' as owned by integer column 'system_cache(id)', assuming SERIAL and omitting
    2014-1129 10:54:28 INFO - anyblok:anyblok.registry - Initialize 'Model' entry
    2014-1129 10:54:29 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Install the blok 'employee'
    2014-1129 10:54:29 INFO - anyblok:root - Registry.reload
    2014-1129 10:54:29 INFO - anyblok:root - Registry.load
    2014-1129 10:54:29 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-1129 10:54:29 INFO - anyblok:anyblok.registry - Blok 'office' loaded
    2014-1129 10:54:29 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-1129 10:54:29 INFO - anyblok:anyblok.registry - Blok 'employee' loaded
    2014-1129 10:54:29 INFO - anyblok:anyblok.registry - Blok 'employee-position' loaded
    2014-1129 10:54:29 INFO - anyblok:anyblok.registry - Assemble 'Model' entry
    2014-1129 10:54:29 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-1129 10:54:29 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-1129 10:54:29 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'system_cache_id_seq' as owned by integer column 'system_cache(id)', assuming SERIAL and omitting
    2014-1129 10:54:29 INFO - anyblok:alembic.autogenerate.compare - Detected added column 'employee.position_name'
    2014-1129 10:54:29 WARNING - anyblok:anyblok.migration - (IntegrityError) column "position_name" contains null values
    'ALTER TABLE employee ALTER COLUMN position_name SET NOT NULL' {}
    2014-1129 10:54:29 INFO - anyblok:anyblok.registry - Initialize 'Model' entry
    2014-1129 10:54:29 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Install the blok 'employee-position'
    2014-1129 10:54:30 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'anyblok-core'
    2014-1129 10:54:30 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'office'
    2014-1129 10:54:30 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'position'
    2014-1129 10:54:30 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'employee'
    2014-1129 10:54:30 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'employee-position'
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Get the employee ...
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Sandrine Chaufournais in Room 308 at 14-16 rue Soleillet 75020 Paris (Administrative Manager)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Christophe Combelles in Room 308 at 14-16 rue Soleillet 75020 Paris (CEO)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Clovis Nzouendjou in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Florent Jouatte in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Simon André in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Jean-Sébastien Suzanne in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Georges Racinet in Room 308 at 14-16 rue Soleillet 75020 Paris (CTO)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Pierre Verkest in Room 308 at 14-16 rue Soleillet 75020 Paris (Project Manager)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - Franck Bret in Room 308 at 14-16 rue Soleillet 75020 Paris (Project Manager)
    2014-1129 10:54:30 INFO - anyblok:exampleblok.scripts - End ...


The registry is loaded twice:

* The first load installs the bloks ``anyblok-core``, ``office``, ``position`` and ``employee``
* The second load installs the conditional blok ``employee-position`` and runs a migration to add the field ``employee_name``

**Call the script again**::

    jssuzanne:anyblok jssuzanne$ ./bin/exampleblok -c anyblok.cfg --message-before "Get the employee ..." --message-after "End ..."
    2014-1129 10:57:52 INFO - anyblok:root - Registry.load
    2014-1129 10:57:52 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-1129 10:57:52 INFO - anyblok:anyblok.registry - Blok 'office' loaded
    2014-1129 10:57:52 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-1129 10:57:52 INFO - anyblok:anyblok.registry - Blok 'employee' loaded
    2014-1129 10:57:52 INFO - anyblok:anyblok.registry - Blok 'employee-position' loaded
    2014-1129 10:57:52 INFO - anyblok:anyblok.registry - Assemble 'Model' entry
    2014-1129 10:57:52 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-1129 10:57:52 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-1129 10:57:52 INFO - anyblok:alembic.ddl.postgresql - Detected sequence named 'system_cache_id_seq' as owned by integer column 'system_cache(id)', assuming SERIAL and omitting
    2014-1129 10:57:52 INFO - anyblok:alembic.autogenerate.compare - Detected NOT NULL on column 'employee.position_name'
    2014-1129 10:57:52 INFO - anyblok:anyblok.registry - Initialize 'Model' entry
    2014-1129 10:57:52 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'anyblok-core'
    2014-1129 10:57:52 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'office'
    2014-1129 10:57:52 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'position'
    2014-1129 10:57:52 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'employee'
    2014-1129 10:57:52 INFO - anyblok:anyblok.bloks.anyblok_core.declarations.system.blok - Load the blok 'employee-position'
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Get the employee ...
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Sandrine Chaufournais in Room 308 at 14-16 rue Soleillet 75020 Paris (Administrative Manager)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Christophe Combelles in Room 308 at 14-16 rue Soleillet 75020 Paris (CEO)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Clovis Nzouendjou in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Florent Jouatte in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Simon André in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Jean-Sébastien Suzanne in Room 308 at 14-16 rue Soleillet 75020 Paris (Developer)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Georges Racinet in Room 308 at 14-16 rue Soleillet 75020 Paris (CTO)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Pierre Verkest in Room 308 at 14-16 rue Soleillet 75020 Paris (Project Manager)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - Franck Bret in Room 308 at 14-16 rue Soleillet 75020 Paris (Project Manager)
    2014-1129 10:57:52 INFO - anyblok:exampleblok.scripts - End ...

The registry is loaded only once, because the bloks are already installed


Builtin generic scripts
+++++++++++++++++++++++

Anyblok provides some helper generic console scripts out of the box:

* anyblok_createdb
* anyblok_updatedb
* anyblok_interpreter
  .. note::

      if IPython is in the sys.modules then the interpreter is an IPython interpreter

* anyblok_nose (nose test)

TODO: I know it's not a setuptools documentation but it could be kind to show
a complete minimalist exampe of `setup.py` with requires (to anyblok).
We could also display the full tree from root

A direct link to download the full working example.

.. _basedoc_tests:

Writing and launching tests
---------------------------

We want to foster a very test friendly culture in the AnyBlok
community, that's why we cover tests writing and launching in this
"Basic usage" page.

That being said, such a dynamic framework represent a challenge for
tests, because the application constructs, e.g., application Models,
must *not* be imported directly. Instead, a proper Registry must be
set up one way or another before the test launcher kicks in, and that
interferes wildly with coverage reports.

Also, the Anyblok Registry being tightly tied to a database, we need
to set it up before hand (most common in application tests) or manage
it from the tests (mostly meant for the framework tests, but could
find its use for some applications or middleware).

.. note:: all of this means that the tests we're discussing aren't
          stricto sensu unit tests, but rather integration
          tests. Nevertheless, we casually speak of them as unit tests
          if they stay lightweight and are about testing individual
          AnyBlok
          components.

          Nothing prevents application developers to also write true unit
          tests, perhaps for subroutines that don't interact with the
          database at all.

To address these challenges, AnyBlok ships with helper base classes
(see below), and provides two different ways to lauch the tests, both based
on `nose <https://pypi.python.org/pypi/nose/1.3.7>`_.

.. _basedoc_testcases:

Writing tests
+++++++++++++

The most commonly used helper base class is :class:`BlokTestCase
<anyblok.tests.testcase.BlokTestCase>`. It provides everything Blok
developers need for their daily workflow: a working registry is setup
once for the whole test run, is exposed as a class attribute,
and the tests are insulated by rollbacking the database transaction.

We should also mention :class:`DBTestCase
<anyblok.tests.testcase.DBTestCase>`, which is more suited for
code that interacts at a deeper level with
the framework (including the framework itself). It creates and drops
the database for each test case, and therefore makes the whole run
terribly slow, but that's sometimes a price worth paying.

.. warning:: One must separate the launches of BlokTestCases
             and of DBTestCases in different runs.


Launching tests with the nose plugin
++++++++++++++++++++++++++++++++++++

Summary: use this if you need accurate coverage results. This is a
good fit for Continuous Integration (CI).

AnyBlok comes with a `nose <https://pypi.python.org/pypi/nose/1.3.7>`_
plugin right away. Once the testing database is set up, and described
by proper environment variables or :ref:`default configuration files
<basedoc_conf_files_default>`, you can test your bloks with the
``--with-anyblok-bloks`` option.

.. warning:: don't use this if you need advanced tests selection
             such as replaying failed tests, or cherry picking one
             specific test which triggers imports that are unwanted
             before the registry is set up.

             Prefer :ref:`anyblok_nose <basedoc_anyblok_nose>` in that case.

Here's an example, adapted from AnyBlok's ``.travis.yml``::

  export ANYBLOK_DATABASE_URL=postgresql:///travis_ci_test
  anyblok_createdb --install-all-bloks
  nosetests anyblok/bloks --with-anyblok-bloks -v -s --with-coverage --cover-package=anyblok

In case the ``coverage`` plugin is also in use, as in the example
above, Anyblok's nose plugin will
perform all Blok loadings and Model final classes assemblies (i.e.,
loads of ``BlokManager`` and ``RegistryManager``) *after* the
``coverage`` startup, thus giving you correct coverage results)

.. note:: If you want to test several Bloks depending on each other, while
          making sure the tests of the lower ones don't need the upper ones
          being installed, and still maintain proper coverage results, you can
          do it with several runs.

          For an example of this, see `anyblok_wms_base/.travis.yml
          <https://github.com/AnyBlok/anyblok_wms_base/blob/master/.travis.yml>`_

.. _basedoc_anyblok_nose:

Launching tests with ``anyblok_nose``
+++++++++++++++++++++++++++++++++++++
Summary: use this if you want the full tests selection capabilities of
nosetests, and don't care about coverage. This is a good fit for
development and debug workflows.

AnyBlok provides the ``anyblok_nose`` script right out of the
box. It takes care of all needed AnyBlok initialization, and *only
then* invokes the nose launcher.

This is the most respectful way of nose internals, but ``coverage`` is
blind with respect to any code imported or run during the Registry
setup. You can use it with ``--failed``, cherry pick any specific test
without worrying whether that'll trigger ``nose`` importing a
declaration class before the Registry, etc.


Synopsis::

  anyblok_nose [ANYBLOK OPTIONS...] -- [NOSE ARGUMENTS...]

Typical usage is with a ``configuration file <basedoc_conf_files>``
(this example also demonstrate the usage of more nose options)::

  anyblok_nose -c mytest.cfg -- workapp/employee_blok --with-doctest --failed --pdb

.. _basedoc_conf_files:

Configuration files
-------------------

Custom or builtin AnyBlok console scripts accept the ``-c`` parameter,
to specify a configuration file instead of passing all the options in the
command line. Example::

  anyblok_createdb -c myapp.cfg


Syntax
++++++

The configuration file allow to load all the initialisation variable::

    [AnyBlok]
    key = value

You can extend an existing config file::

    [AnyBlok]
    extend = ``path of the configfile``

The logging configuration are also loaded, see `logging configuration file format
<https://docs.python.org/3/library/logging.config.html#configuration-file-format>`_::

    [AnyBlok]
    logging_configfile = ``name of the config file``
    # json_logging_configfile = logging config file write with json
    # yaml_logging_configfile = logging config file write with yaml

    loggers]
    keys=root,anyblok

    [handlers]
    keys=consoleHandler

    [formatters]
    keys=consoleFormatter

    [logger_root]
    level=INFO
    handlers=consoleHandler

    [logger_anyblok]
    level=INFO
    handlers=consoleHandler
    qualname=anyblok
    propagate=1

    [handler_consoleHandler]
    class=StreamHandler
    level=INFO
    formatter=consoleFormatter
    args=(sys.stdout,)

    [formatter_consoleFormatter]
    class=anyblok.logging.consoleFormatter
    format=%(database)s:%(levelname)s - %(message)s
    datefmt=

.. _basedoc_conf_files_default:

Default configuration files
+++++++++++++++++++++++++++

You can define default *system* or *user* configuration file in fonction of
your *OS*:

* *linux*
    - *system*: /etc/xdg/AnyBlok/conf.cfg
    - *user*: /home/``user name``/.config/AnyBlok/conf.cfg
* *mac os x*
    - *system*: /Library/Application Support/AnyBlok/conf.cfg
    - *user*: /Users/``user name``/Library/Application Support/AnyBlok/conf.cfg

.. note::

    Works also for *windows*, See https://pypi.python.org/pypi/appdirs. The
    entry used are:

    * *system*: site_config_dir
    * *user*: user_config_dir

Theses configuration files are loaded before the specific configuration file. If
the configuration file does not exist then it will not raise error
