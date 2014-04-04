README
======

AnyBlok is a framework to include dynamicly Python source. It is the reference 
documentation.

This first part present How create an application with his own code. Why have 
you to create an application? Because AnyBlok is an framework not an application

And the goal more than one application use the same database for diferent goal.
The web server need to give acces to the user, but a profiler need another 
access with another access rule, or another application need to follow one part
of the functionnality.

We will write a simple application which connect to an existing database:

* Worker
    - Have a name
    - Have a desk(Room)
    - Can have a position
* Room
    - Have a number
    - Have an address
    - have workers
* Adress
    - Have a street
    - have a zipcode
    - have a city
    - have rooms
* Position
    - Have a name

Create your Blok group
----------------------

A blok group is a ``setuptools`` entry point. Separate the project by group
allow to select the bloks needed by the application. And multiply the posiibility
A blok come from more than 1 blok group, it is not the same blok but they have
the same name. You can have two implementation for the same thing and use the
good implementation in the context.

For this example, the blok group ``WorkBlok`` will be used

Create Your Blok
----------------

A blok is a set of AnyBlok:

* Model: Python class usable by the application and linked in the registry
* Mixin: Python class to extend Model
* Column: Python class, describe a type of sql column
* RelationShip: Python class, allow to surh on the join on the model data
* ...

The blok name must be declare in the blok group of the distribution::

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

And the blok must inherit of the Blok class of anyblok in the ``__init__.py`` 
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
            for position in ('DG', 'Cormercial', 'Secrétaire', 'Chef de projet',
                             'Developper'):
                self.registry.Position.insert(name=position)

    # position.py describe the model Position 

Some blok can have requirement. Each blok define this dependences:

* required: the blok must be loaded before
* optional: If the blok exist, it will be loaded

A blok can be declared ``autoinstall`` if the blok is not install at the load
of the registry, then this blok will be loaded and installed

**Worker blok**::

    # tree

    worker_blok
    ├── __init__.py
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
            for worker in ('Georges Racinet', 'Christophe Combelles',
                           'Sandrine Chaufournais', 'Pierre Verkest',
                           u"Simon André", 'Florent Jouatte', 'Clovis Nzouendjou',
                           u"Jean-Sébastien Suzanne"):
                self.registry.Worker.insert(name=worker, room=room)

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

The Model must be added under the node Model of the registry with the 
class decorator ``AnyBlok.target_registry``::

    from AnyBlok import target_registry, Model

    @target_registry(Model)
    class AAnyBlokModel:
        """ The first Model of our application """


They are two type of Model:

* SQL: Génerate a table in database
* No SQL: No table but the model exist in the registry and can be used.

A SQL model can define the column by adding a column::

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import String

    @target_registry(Model)
    class ASQLModel:

        acolumn = String(label="The first column", primary_key=True)

.. warning::
    All SQL Model must have one or more primary_key

.. warning::
    The table name depend of the registry tree, here the table is ``asqlcolumn``.
    If a new model are define under ASQLModel (example UnderModel: 
    ``asqlcolumn_undermodel``)

**desk_blok.desk**::

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import String, Integer
    from AnyBlok.RelationShip import Many2One


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
                           remote_column="id", one2many="rooms")

        def __str__(self):
            return "Room %d at %s" % (self.number, self.address)

The relationships can also define the opposite relation, here the Many2One
declare the One2Many rooms on the Address Model

A relationship Many2One or One2One must have an existing column.
The attribute ``column_name`` alow to choose the column linked, if this
attribute is missing then the value is "'model.table'.'remote_column'"
If the column linked doesn't exist then the relationship create the 
column with the same type of the remote_column

**position_blok.position**::

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import String


    @target_registry(Model)
    class Position:

        name = String(label="Position", primary_key=True)

        def __str__(self):
            return self.name

**worker_blok.worker**::

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import String, Integer
    from AnyBlok.RelationShip import Many2One


    @target_registry(Model)
    class Worker:

        name = String(label="Number of the room", primary_key=True)
        room = Many2One(label="Desk", model=Model.Room, remote_column="id"
                        one2many="workers")

        def __str__(self):
            return "%s in %s" % (self.name, self.room)


Update an existing Model
------------------------

If you create 2 models with the same registry position, the same name, then the
second model subclass the first model. And the two models will be merge to 
get the real model

**worker_position_blok.worker**::

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import String
    from AnyBlok.RelationShip import Many2One


    @target_registry(Model)
    class Worker:

        position = Many2One(label="Position", model=Model.Position,
                            remote_column="name")

        def __str__(self):
            res = super(Worker, self).__str__()
            return "%s (%s)" % (res, self.position)


Create Your application
-----------------------

.. warning:: TODO
