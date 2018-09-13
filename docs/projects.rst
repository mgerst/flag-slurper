Projects
========
Flag slurper has the concept of "projects". These projects tell flag slurper where to find various files such as the
``teams.yml`` and ``services.yml`` files. It may also contain other configuration options such as where flags are
located. The primary purpose of the project system is to keep data from different :term:`CDCs <CDC>` separate.

To create a project, run:

.. code-block:: bash

    flag-slurper project init --base ~/cdcs/isu2-18 --name "ISU2 2018"

This will create a project named "ISU2 2018" in the folder ``~/cdcs/isu2-18``. You can then run the following command to
activiate the project.

.. code-block:: bash

    eval $(flag-slurper project env ~/cdcs/isu2-18)

.. note::

    The output of the ``env`` command will set the ``SLURPER_PROJECT`` environment variable. This variable can also be
    set manually, instead of the ``--project`` flag.

When you want to deactivate a project, run the ``unslurp`` command.

Alternatively, you can specify ``--project PATH`` on each command. For example:

.. code-block:: bash

    flag-slurper --project ~/cdcs/isu2-18/ autopwn generate

.. note::

    The ``--project PATH`` flag must be before any subcommands.

Flags
-----
The Auto PWN feature will automatically look in common directories for :term:`flags <flag>` that look like a flag. You
can also specify locations to check. The following project file defines the "Web /root flag":

.. code-block:: yaml

    _version: "1.0"
    project: ISU2 2018
    base: ~/cdcs/isu2-18
    flags:
      - service: WWW SSH
        type: blue
        location: /root
        name: "team{{ num }}_www_root.flag"
        search: yes

You can specify as many flags as you want. All of the following fields are required:

**service**
    The name of the service this flag is associated with. Auto PWN matches against this when determining what flags it
    should look for when attacking a service.
**type**
    Which flag type this is ``blue`` (read) or ``red`` (write). Currently only ``blue`` is supported.
**location**
    The directory the flag is supposed to be located in.
**name**
    The expected file name of the flag. Pay close attention to ``{{ num }}``. This is a placeholder that will be
    replaced with the team number during the attack.
**search**
    Whether Auto PWN should search ``location`` for any files that are roughly the correct file size. A search is only
    performed if the falg is not found at it's exact name ``{{ location }}/{{ name }}``.

Here's an example of an Auto PWN run that obtained flags:

.. image:: https://asciinema.org/a/SZK8Ma0lUzX8H1CE02sLOjVIT.png
    :target: https://asciinema.org/a/SZK8Ma0lUzX8H1CE02sLOjVIT

Credentials
-----------
Credentails can be managed through the ``creds`` subcommand. To add a credential:

.. code-block:: bash

    flag-slurper creds add root cdc

List credentials:

.. code-block:: bash

    flag-slurper creds ls

Remove credential:

.. code-block:: bash

    flag-slurper creds rm root cdc

Show details for a credential

.. code-block:: bash

    flag-slurper creds show root:cdc
