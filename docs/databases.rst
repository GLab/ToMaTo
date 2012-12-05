Databases
=========

The ToMaTo backend needs a database to store information about hosts, topologies and users. The choice of this database is important for the performance of the ToMaTo backend.

ToMaTo uses Django as a database backend so the `Django database documentation <https://docs.djangoproject.com/en/dev/ref/databases/>`_ applies to ToMaTo as well. 


SQLite
------
Note that SQLite lacks some features of real databases and thus is not suitable for running or developing ToMaTo.


PostgreSQL
----------

PostgreSQL is the database that is used in the German-Lab installation. It is a full-featured database with good performance.

Raising the connection limit
****************************

The default database connection limit of PostgreSQL is set to 100 which can be reached by ToMaTo if several users are running a lot tasks in parallel. In the config file ``postgresql.conf`` the value ``max_connections`` can be raised to allow more concurrent connections. If the postgres server then hits the shared memory limit, the sysctl value ``kernel.shmmax`` needs to be increased. (See `the PostgreSQl documentation <http://www.postgresql.org/docs/current/static/kernel-resources.html>`_ for more details.)


Exporting and importing the ToMaTo data
---------------------------------------

The ``manage.py`` script that comes with the ToMaTo backend can be used to dump and load the database contents in a generic database-agnostic format. These commands might only work when run as user ``tomato``, so ``sudo -u tomato ./manage.py ...``. Also note that the commands only work when the database is up-to-date with the current layout in the code. (See migration for details)

Dumping the database
********************

The following command dumps the database to a file named ``dump.json`` in the current directory::

   $ ./manage.py dumpdata tomato south > dump.json


Loading the data into the database
**********************************

The following command load a dump from a file named ``dump.json`` into the database. (Note that the file extension must be skipped in this command) ::

   $ ./manage.py loaddata dump

Database migrations
-------------------

As the database layout of ToMaTo changes, the database must be migrated to the new layout. ToMaTo automatically migrates old database schemas to the newest one. (Backups should still be made before the migration.)