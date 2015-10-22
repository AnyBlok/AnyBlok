.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. contents::

How to create your own application
==================================

This first part introduces how to create an application with his code.
Why do we have to create an application ? Because AnyBlok is just a framework
not an application.

The goal is that more than one application can use the same database for different usage.
The web server needs to give access to the user, but a profiler needs another
access with another access rule, or another application needs to provide one part
of the functionnalities.

We will write a simple application that connects to a new empty database:

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

Declare bloks in the entry points
---------------------------------

A blok must be declared in a ``setuptools`` entry point named **bloks**.

File tree::

    WorkBlok
    └── setup.py


We declare 4 bloks in the ``setup.py`` file that we will define explain after::

    bloks = [
        'office=exampleblok.office_blok:OfficeBlok',
        'employee=exampleblok.employee_blok:EmployeeBlok',
        'position=exampleblok.position_blok:PositionBlok',
        'employee-position=exampleblok.employee_position_blok:EmployeePositionBlok',
    ],

    setup(
        # (...)
        entry_points={
            'bloks': bloks,
        },
    )

Create Bloks
------------

A blok contains Declarations such as:

* Model: a Python class usable by the application and linked in the registry
* Mixin: a Python class to extend Model
* Column: a Python class, describing an sql column type
* RelationShip: a Python class, allowing to surh on the join on the model data
* ...

The blok name must be declared in the blok group of the ``setup.py`` file of
the distribution as explain before.

And the blok must inherit the Blok class of anyblok in the ``__init__.py``
file of a package::

    from anyblok.blok import Blok

    class MyFirstBlok(Blok):
        """ This is valid blok """

The blok class must be in the init file of the package so that all modules and
sub-packages which have declarations have to be imported by anyblok, in the
**import_declaration_module** method


**Office blok**

File tree::

    office_blok
    ├── __init__.py
    └── office.py

``__init__.py`` file::

    from anyblok.blok import Blok


    class OfficeBlok(Blok):

        version = '1.0.0'

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
            from . import office  # noqa

    # office.py describe the models Address and Room

**Position blok**

File tree::

    position_blok
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

    # position.py describe the model Position

**Employee blok**

Some bloks can have requirements. Each blok define its dependencies:

* required: required bloks must be loaded before
* optional: If the blok exists, optional bloks will be loaded

A blok can be declared as ``autoinstall`` if the blok is not installed upon the loading
of the registry, then this blok will be loaded and installed.

File tree::

    employee_blok
    ├── __init__.py
    ├── config.py
    └── employee.py

``__init__.py`` file::

    from anyblok.blok import Blok


    class EmployeeBlok(Blok):

        version = '1.0.0'
        autoinstall = True

        required = [
            'office',
        ]

        optional = [
            'position',
        ]

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
                                          u"Jean-Sébastien Suzanne")]
            self.registry.Employee.multi_insert(*employees)

        def update(self, latest_version):
            if latest_version is None:
                self.install()

        @classmethod
        def import_declaration_module(cls):
            from . import config  # noqa
            from . import employee  # noqa

    # employee.py describe the model Employee

**EmployeePosition blok**:

Some bloks can be installed when other bloks are installed, they are
called conditional bloks.

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

Create Models
-------------

The Model must be added under the Model node of the declaration with the
class decorator ``Declarations.register``::

    from anyblok import Declarations

    @Declarations.register(Declarations.Model)
    class AAnyBlokModel:
        """ The first Model of our application """


There are two types of Model:

* SQL: Create a table in the database (inherit SqlBase and Base)
* Non SQL: No table but the model exists in the registry and can be used (inherits Base).

SqlBase and Base are core models. Directly calling them is not allowed.
But they are inheritable and each subclass is propagated to all the anyblok
models. This example uses ``insert`` and ``multi_insert`` added by the
``anyblok-core`` blok.

An SQL model can define columns::

    from anyblok import Declarations
    from anyblok.column import String

    register = Declarations.register
    Model = Declarations.Model


    @register(Model)
    class ASQLModel:

        acolumn = String(label="The first column", primary_key=True)

.. warning::
    Any SQL Model must have a primary key composed with one or more columns.

.. warning::
    The table name depends on the registry tree. Here the table is ``asqlmodel``.
    If a new model is defined under ASQLModel (example UnderModel:
    ``asqlcolumn_undermodel``), the registry model will be stored
    as Model.ASQLModel.UnderModel

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
also declares the ``room`` One2Many relation on the Address Model

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


Updating an existing Model
--------------------------

If you create 2 models with the same declaration position and the same name, the
second model will subclass the first model. The two models will be merged to
get the real model

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


Add entries in the argparse configuration
-----------------------------------------

Some applications may require options. Options are grouped by
category. And the application chooses the option category to display.

**employee_blok.config**::

    from anyblok.config import Configuration


    @Configuration.add('message', label="This is the group message")
    def add_interpreter(parser, configuration):
        parser.add_argument('--message-before', dest='message_before')
        parser.add_argument('--message-after', dest='message_after')


Create an application
---------------------

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


Generic application of AnyBlok
------------------------------

Anyblok provides some console script to help :

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

AnyBlok plugin for nosetests
----------------------------

You can test your bloks in your anyblok distribution with nose. use the option
*--with-anyblok-bloks*. The plugin load the ``BlokManager`` et the
``RegistryManager`` after load the ``coverage`` plugin.


Create the configuration file
-----------------------------

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

Default configuration file
--------------------------

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

Theses configuration files are load before the specific configuration file. If
the the configuration file does not exist then it will not raise error
