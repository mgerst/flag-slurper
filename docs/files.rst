Files
=====
Flag slurper contains a database of files found on competitior machines. This is normally populated by the
`AutoPWN <autopwn_overview>`_ functionality. All file commands require that a `Project <projects>`_ is set.

Usage
-----
The main command you'll use is listing all files in the database.

.. code-block:: bash

    flag-slurper files ls

The ``ls`` command can be filtered by team number (``-t TEAM``), file name (``-n NAME``), and/or service
name (``-s SERVICE``).

Once you find a file you want to see, you can use the ``show`` command. This will display metadata on the file
and will then open the file in your text editor if it is a text file.

.. code-block:: bash

    flag-slurper files show 1

You may also save the file directly from the database to the given file path.

.. code-block:: bash

    flag-slurper files get 1 ~/team1_shadow

If you don't want to keep a file around any more, you can remove it.

.. code-block:: bash

    flag-slurper files rm 1

Example
-------
.. image:: https://asciinema.org/a/uCV0jU7XEQpOUFFmaL5mp1bkq.png
    :target: https://asciinema.org/a/uCV0jU7XEQpOUFFmaL5mp1bkq
