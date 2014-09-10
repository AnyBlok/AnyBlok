README
======

AnyBlok is a framework to dynamically include Python sources. It is the reference
documentation.

This first part presents how to create an application with his own code. Why do we have to
create an application ? Because AnyBlok is just a framework not an application.

And the goal more than one application use the same database for different goal.
The web server need to give access to the user, but a profiler need another
access with another access rule, or another application needs to follow one part
of the functionnality.

We will write a simple application which connect to an existing database:

* Worker
    - name: worker name
    - desk (Room): the room where the worker works
    - position: worker position (manager, employee...)
* Room
    - number: discribe the room in the office
    - address: postal address
    - workers: men and women working in that room
* Address
    - street
    - zipcode
    - city
    - rooms: room list
* Position
    - name: position name

Create your Blok group
----------------------

A blok group is a ``setuptools`` entry point. Separate the project by group
allows to select the bloks needed by the application. This separation also allows
a blok to come from more than one blok group, it is not the same blok but they have
the same name. You can have two implementations for the same thing and use the
good implementation depending on the context.

For this example, the blok group ``WorkBlok`` will be used

Create Your Blok
----------------

A blok is a set of Declaration

* Model: Python class usable by the application and linked in the registry
* Mixin: Python class to extend Model
* Column: Python class, describe a type of sql column
* RelationShip: Python class, allow to surh on the join on the model data
* ...

The blok name must be declared in the blok group of the distribution::

    # declare 4 bloks
    # desk: is the location
    * worker: is the person
    * position: is the position type
    * worker-position: link a person with a position
    WorkBlok = [
        'desk=exampleblok.desk_blok:DeskBlok',
        'worker=exampleblok.worker_blok:WorkerBlok',
        'position=exampleblok.position_blok:PositionBlok',
        'worker-position=exampleblok.worker_position_blok:WorkerPositionBlok',
    ],

    setup(
        # ...
        entry_points={
            'WorkBlok': WorkBlok,
        },
    )

And the blok must inherits of the Blok class of anyblok in the ``__init__.py``
file of a package::

    from anyblok.blok import Blok

    class MyFirstBlok(Blok):
        """ This is valid blok """

The blok class must be in the init of the package because all the module and
package in this package will be import by anyblok.

.. warning::
    The modules and package start with ``_`` aren't imported, the package tests
    are not imported to because the test haven't to import with blok

**Desk blok**::

    # tree

    desk_blok
    ├── __init__.py
    └── desk.py

    # __init__.py

    from anyblok.blok import Blok


    class DeskBlok(Blok):

        def install(self):
            """ this method is call at the installation of this blok """
            address = self.registry.Address.insert(street='14-16 rue Soleillet',
                                                   zip='75020', city='Paris')
            self.registry.Room.insert(number=308, address=address)

    # desk.py describe the models Address and Room

**Position blok**::

    # tree

    position_blok
    ├── __init__.py
    └── position.py

    # __init__.py

    from anyblok.blok import Blok


    class PositionBlok(Blok):

        def install(self):
            self.registry.Position.multi_insert({'name': 'DG'},
                                                {'name': 'Comercial'},
                                                {'name': 'Secrétaire'},
                                                {'name': 'Chef de projet'},
                                                {'name': 'Developper'})

    # position.py describe the model Position

Some blok can have requirement. Each blok define this dependencies:

* required: the blok must be loaded before
* optional: If the blok exist, it will be loaded

A blok can be declared ``autoinstall`` if the blok is not installed upon the loading
of the registry, then this blok will be loaded and installed

**Worker blok**::

    # tree

    worker_blok
    ├── __init__.py
    ├── argsparse.py
    └── worker.py

    # __init__.py

    from anyblok.blok import Blok


    class WorkerBlok(Blok):

        autoinstall = True

        required = [
            'desk',
        ]

        optional = [
            'position',
        ]

        def install(self):
            room = self.registry.Room.query().filter(
                self.registry.Room.number == 308).first()
            workers = [dict(name=worker, room=room)
                       for worker in ('Georges Racinet', 'Christophe Combelles',
                                      'Sandrine Chaufournais', 'Pierre Verkest',
                                      u"Simon André", 'Florent Jouatte',
                                      'Clovis Nzouendjou',
                                      u"Jean-Sébastien Suzanne")]
            self.registry.Worker.multi_insert(*workers)

    # worker.py describe the model Worker

Some blok can be auto installed because other blok are installed, it is the
conditional blok.

**WorkerPosition blok**::

    # tree

    worker_position_blok
    ├── __init__.py
    └── worker.py

    # __init__.py

    from anyblok.blok import Blok


    class WorkerPositionBlok(Blok):

        priority = 200

        conditional = [
            'worker',
            'position',
        ]

        def install(self):
            Worker = self.registry.Worker

            position_by_worker = {
                'Georges Racinet': 'DG',
                'Christophe Combelles': 'Comercial',
                'Sandrine Chaufournais': u"Secrétaire",
                'Pierre Verkest': 'Chef de projet',
                u"Simon André": 'Developper',
                'Florent Jouatte': 'Developper',
                'Clovis Nzouendjou': 'Developper',
                u"Jean-Sébastien Suzanne": 'Developper',
            }

            for worker, position in position_by_worker.items():
                Worker.query().filter(Worker.name == worker).update({
                    'position_name': position})

.. warning::
    They are not strongly dependancies linked between conditional bloks and
    the blok, so the priority must be increase, The blok are load by dependencie
    and priority a blok with small dependancie will be loaded before a blok with
    higth dependancie

Create Your Model
-----------------

The Model must be added under the node Model of the declaration with the
class decorator ``Declarations.target_registry``::

    from anyblok import Declarations

    @Declarations.target_registry(Declarations.Model)
    class AAnyBlokModel:
        """ The first Model of our application """


They are two type of Model:

* SQL: Generate a table in the database (inherit SqlBase and Base)
* No SQL: No table but the model exist in the registry and can be used (inherit Base).

SqlBase and Base are core models, directly call them is now allowed, too low level,
but they are subclassable and each subclasses are propagated to all the anyblok
models. this example use ``insert`` and ``multi_insert`` adding by ``anyblok-core`` blok.

A SQL model can define the columns by adding a column::

    from anyblok import Declarations
    target_registry = Declarations.target_registry
    Model = Declarations.Model
    String = Declarations.Column.String

    @target_registry(Model)
    class ASQLModel:

        acolumn = String(label="The first column", primary_key=True)

.. warning::
    All SQL Model must have one or more primary_key

.. warning::
    The table name depend of the registry tree, here the table is ``asqlcolumn``.
    If a new model are define under ASQLModel (example UnderModel:
    ``asqlcolumn_undermodel``) and the registry model is Model.ASQLModel.UnderModel

**desk_blok.desk**::

    from anyblok import Declarations
    target_registry = Declarations.target_registry
    Model = Declarations.Model
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One


    @target_registry(Model)
    class Address:

        id = Integer(label="Identifying", primary_key=True)
        street = String(label="Street", nullable=False)
        zip = String(label="Zip", nullable=False)
        city = String(label="City", nullable=False)

        def __str__(self):
            return "%s %s %s" % (self.street, self.zip, self.city)


    @target_registry(Model)
    class Room:

        id = Integer(label="Identifying", primary_key=True)
        number = Integer(label="Number of the room", nullable=False)
        address = Many2One(label="Address", model=Model.Address, nullable=False,
                           one2many="rooms")

        def __str__(self):
            return "Room %d at %s" % (self.number, self.address)

The relationships can also define the opposite relation, here the Many2One
declare the One2Many rooms on the Address Model

A relationship Many2One or One2One must have an existing column.
The attribute ``column_name`` allow to choose the column linked, if this
attribute is missing then the value is "'model.table'.'remote_column'"
If the column linked doesn't exist then the relationship create the
column with the same type of the remote_column

**position_blok.position**::

    from anyblok import Declarations
    target_registry = Declarations.target_registry
    Model = Declarations.Model
    String = Declarations.Column.String


    @target_registry(Model)
    class Position:

        name = String(label="Position", primary_key=True)

        def __str__(self):
            return self.name

**worker_blok.worker**::

    from anyblok import Declarations
    target_registry = Declarations.target_registry
    Model = Declarations.Model
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One


    @target_registry(Model)
    class Worker:

        name = String(label="Number of the room", primary_key=True)
        room = Many2One(label="Desk", model=Model.Room, one2many="workers")

        def __str__(self):
            return "%s in %s" % (self.name, self.room)


Update an existing Model
------------------------

If you create 2 models with the same declaration position, the same name, then the
second model subclass the first model. And the two models will be merged to
get the real model

**worker_position_blok.worker**::

    from anyblok import Declarations
    target_registry = Declarations.target_registry
    Model = Declarations.Model
    Many2One = Declarations.RelationShip.Many2One


    @target_registry(Model)
    class Worker:

        position = Many2One(label="Position", model=Model.Position, nullable=False)

        def __str__(self):
            res = super(Worker, self).__str__()
            return "%s (%s)" % (res, self.position)


Add entries in the argsparse configuration
------------------------------------------

For some application some option can be needed. Options are grouped by
category. And the application choose the category option to display.

**worker_blok.arsparse**::

    from anyblok._argsparse import ArgsParseManager


    @ArgsParseManager.add('message', label="This is the group message")
    def add_interpreter(parser, configuration):
        parser.add_argument('--message-before', dest='message_before')
        parser.add_argument('--message-after', dest='message_after')


Create your application
-----------------------

The application can be a simple script or a setuptools script. For a setuptools
script add in setup::

    setup(
        ...
        entry_points={
            'console_scripts': ['exampleblok=exampleblok.scripts:exampleblok'],
            'WorkBlok': WorkBlok,
        },
    )

The script must display:

* the ``message_before`` is filled
* the lists of the worker by address and by room
* the ``message_after`` is filled

**script**::

    import anyblok
    from logging import getLogger
    from anyblok._argsparse import ArgsParseManager

    logger = getLogger(__name__)


    def exampleblok():
        # Initialise the application, with a name and a version number
        # select the groupe of options to display
        # select the groups of bloks availlable
        # return a registry if the database are selected
        registry = anyblok.start(
            'Example Blok', '1.0',
            argsparse_groups=['config', 'database', 'message'],
            parts_to_load=['AnyBlok', 'WorkBlok'])

        if not registry:
            return

        message_before = ArgsParseManager.get('message_before')
        message_after = ArgsParseManager.get('message_after')

        if message_before:
            logger.info(message_before)

        for address in registry.Address.query().all():
            for room in address.rooms:
                for worker in room.workers:
                    logger.info(worker)

        if message_after:
            logger.info(message_after)


**Get the help of your application**::

    jssuzanne:anyblok jssuzanne$ ./bin/exampleblok -h
    usage: exampleblok [-h] [-c CONFIGFILE] [--message-before MESSAGE_BEFORE]
                       [--message-after MESSAGE_AFTER] [--db_name DBNAME]
                       [--db_drivername DBDRIVERNAME] [--db_username DBUSERNAME]
                       [--db_password DBPASSWORD] [--db_host DBHOST]
                       [--db_port DBPORT]

    Example Blok - 1.0

    optional arguments:
        -h, --help            show this help message and exit
        -c CONFIGFILE         Relative path of the config file

    This is the group message:
        --message-before MESSAGE_BEFORE
        --message-after MESSAGE_AFTER

    Database:
        --db_name DBNAME      Name of the data base
        --db_drivername DBDRIVERNAME
                              the name of the database backend. This name will
                              correspond to a module in sqlalchemy/databases or a
                              third party plug-in
        --db_username DBUSERNAME
    The user name
        --db_password DBPASSWORD
    database password
        --db_host DBHOST      The name of the host
        --db_port DBPORT      The port number

**Create an empty database and call the script**::

    jssuzanne:anyblok jssuzanne$ createdb anyblok
    jssuzanne:anyblok jssuzanne$ ./bin/exampleblok -c anyblok.cfg --message-before "Get the worker ..." --message-after "End ..."
    2014-0405 23:54:32 INFO - anyblok:root - Registry.load
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'desk' loaded
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'worker' loaded
    2014-0405 23:54:32 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-0405 23:54:32 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-0405 23:54:32 INFO - anyblok:AnyBlok.bloks.anyblok-core.system.blok - Install the blok 'anyblok-core'
    2014-0405 23:54:32 INFO - anyblok:AnyBlok.bloks.anyblok-core.system.blok - Install the blok 'desk'
    2014-0405 23:54:32 INFO - anyblok:AnyBlok.bloks.anyblok-core.system.blok - Install the blok 'position'
    2014-0405 23:54:32 INFO - anyblok:AnyBlok.bloks.anyblok-core.system.blok - Install the blok 'worker'
    2014-0405 23:54:32 INFO - anyblok:root - Registry.upgrade with args (<anyblok.registry.Registry object at 0x10867bcd0>,) and kwargs {'install': ['worker-position']}
    2014-0405 23:54:32 INFO - anyblok:root - Registry.reload
    2014-0405 23:54:32 INFO - anyblok:root - Registry.load
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'desk' loaded
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'worker' loaded
    2014-0405 23:54:32 INFO - anyblok:anyblok.registry - Blok 'worker-position' loaded
    2014-0405 23:54:32 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-0405 23:54:32 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-0405 23:54:32 INFO - anyblok:alembic.autogenerate.compare - Detected added column 'worker.position_name'
    2014-0405 23:54:32 INFO - anyblok:AnyBlok.bloks.anyblok-core.system.blok - Install the blok 'worker-position'
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Get the worker ...
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Florent Jouatte in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Georges Racinet in Room 308 at 14-16 rue Soleillet 75020 Paris (DG)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Pierre Verkest in Room 308 at 14-16 rue Soleillet 75020 Paris (Chef de projet)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Sandrine Chaufournais in Room 308 at 14-16 rue Soleillet 75020 Paris (Secrétaire)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Clovis Nzouendjou in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Jean-Sébastien Suzanne in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Christophe Combelles in Room 308 at 14-16 rue Soleillet 75020 Paris (Comercial)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - Simon André in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:54:32 INFO - anyblok:exampleblok.scripts - End ...


The registry is loaded two time:

* First load install the bloks ``anyblok-core``, ``desk``, ``position`` and ``worker``
* Second load install the conditional blok ``worker-position`` and make a migration to add the field ``worker_name``

**Recall the script**::

    jssuzanne:anyblok jssuzanne$ ./bin/exampleblok -c anyblok.cfg --message-before "Get the worker ..." --message-after "End ..."
    2014-0405 23:58:10 INFO - anyblok:root - Registry.load
    2014-0405 23:58:10 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-0405 23:58:10 INFO - anyblok:anyblok.registry - Blok 'desk' loaded
    2014-0405 23:58:10 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-0405 23:58:10 INFO - anyblok:anyblok.registry - Blok 'worker' loaded
    2014-0405 23:58:10 INFO - anyblok:anyblok.registry - Blok 'worker-position' loaded
    2014-0405 23:58:10 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-0405 23:58:10 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Get the worker ...
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Florent Jouatte in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Georges Racinet in Room 308 at 14-16 rue Soleillet 75020 Paris (DG)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Pierre Verkest in Room 308 at 14-16 rue Soleillet 75020 Paris (Chef de projet)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Sandrine Chaufournais in Room 308 at 14-16 rue Soleillet 75020 Paris (Secrétaire)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Clovis Nzouendjou in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Jean-Sébastien Suzanne in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Christophe Combelles in Room 308 at 14-16 rue Soleillet 75020 Paris (Comercial)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - Simon André in Room 308 at 14-16 rue Soleillet 75020 Paris (Developper)
    2014-0405 23:58:11 INFO - anyblok:exampleblok.scripts - End ...

The registry is loaded only one time, because the bloks are already installed


Create an interpreter
---------------------

Anyblok give some function to help to create application:

* createdb
* updatedb
* interpreter

::

    from anyblok.scripts import interpreter


    def exampleblok_interpreter():
        anyblok_interpreter(
            'Interpreter', '1.0',
            argsparse_groups=['config', 'database', 'interpreter'],
            parts_to_load=['AnyBlok', 'WorkBlok'])

::

    jssuzanne:anyblok jssuzanne$ ./bin/exampleblok_interpretor -c anyblok.cfg
    2014-0428 20:57:38 INFO - anyblok:root - Registry.load
    2014-0428 20:57:38 INFO - anyblok:anyblok.registry - Blok 'anyblok-core' loaded
    2014-0428 20:57:38 INFO - anyblok:anyblok.registry - Blok 'desk' loaded
    2014-0428 20:57:38 INFO - anyblok:anyblok.registry - Blok 'position' loaded
    2014-0428 20:57:38 INFO - anyblok:anyblok.registry - Blok 'worker' loaded
    2014-0428 20:57:38 INFO - anyblok:anyblok.registry - Blok 'worker-position' loaded
    2014-0428 20:57:38 INFO - anyblok:anyblok.registry - Assemble 'Model' entry
    2014-0428 20:57:39 INFO - anyblok:alembic.migration - Context impl PostgresqlImpl.
    2014-0428 20:57:39 INFO - anyblok:alembic.migration - Will assume transactional DDL.
    2014-0428 20:57:39 INFO - anyblok:anyblok.registry - Initialize 'Model' entry
    Python 3.3.5 (default, Mar 12 2014, 15:18:42)
    [GCC 4.2.1 Compatible Apple LLVM 5.1 (clang-503.0.38)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>>
