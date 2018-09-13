Auto PWN
========
Flag Slurper contains a utility for automatically attempting default credentails against teams' SSH hosts. This works by
grabbing the team list from :term:`IScorE` and a list of all the services. The default credentails it uses are:

- ``root:cdc``
- ``cdc:cdc``

Requirements
------------
AutoPWN requires a database. For many cases sqlite will do, but in order to use parallel AutoPWN, a server-based
database (such as postgres) is required. This is due to sqlite only allowing one writer at a time. The database can be
configured in your flagrc file:

.. code-block:: ini

    [database]
    ; For sqlite (default)
    url=sqlite:///{{ project }}/db.sqlite

    ; For postgres
    url=postgres:///splurper

The ``{{ project }}`` variable is the file path to the current project and is optional.

Usage
-----
You first need to create a project and result database:

.. code-block:: bash

    flag-slurper project init -b ~/cdcs/isu2-18 --name "ISU2 2018"
    flag-slurper project create-db

To generate the team and service list you can simply run:

.. code-block:: bash

    flag-slurper autopwn generate

This will cache the team and service lists into the database. This will be used by other ``autopwn`` commands so they
don't need to keep hitting the :term:`IScorE` API during the attack phase when the API is getting hammered.

After generating the local files, you can then pwn all the things!

.. code-block:: bash

    flag-slurper autopwn pwn

This will print out what credentials worked on which machines and any flags found. These results are recorded in the
database and can be viewed like this:

.. code-block:: bash

    flag-slurper autopwn results
