Shadow
======
Flag slurper contains a database of shadow entries extracted from files found on competition machines through the SSH
Exfiltration Post-Plugin. This is normally populated by the `AutoPWN <autopwn_overview>`_ functionality. All shadow
commands require that a `Project <projects>`_ is set.

Usage
-----
The main command you'll use is listed all files in the database.

.. code-block:: bash

    flag-slurper shadow ls

The ``ls`` command can be filtered by team number (``-t TEAM``), service name (``-n NAME``), and/or (``-u USERNAME``).
You may optionally pass a ``-f FORMAT`` option to specify how the output should be formatted. The default is the
``table`` format which will output in a nice ASCII table in a pager. Also provided are the ``hashcat`` or ``text``
formats which output in a textfile format suitable for consumption by tools such as hashcat.
