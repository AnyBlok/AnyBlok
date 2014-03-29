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

We will write a simple application which connect to an existing database
With existing tables:

* Boss
    - Have worker
    - Have a desk
* worker
    - Have a boss
    - Have a desk
* Room
    - Have desk
* desk
    - Have a room
    - have a worker or a boss


Create Your application
-----------------------

.. warning:: TODO

Create Your Blok
----------------

.. warning:: TODO

Create Your Model
-----------------

.. warning:: TODO

Update an existing Model
------------------------

.. warning:: TODO
