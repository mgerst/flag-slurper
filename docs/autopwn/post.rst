Post PWN
========
The AutoPWN functionality can be extended through post pwn plugins. These are plugins that run
against a service *after* the pwn process (gaining access, checking sudo, capturing flags, etc.).
At the time of writing there is one built-in post pwn plugin:

- ``ssh_exfil``

Configuration
-------------
Post pwn plugins are configured through the Project File, but they can also be run automatically
based on decisions made by the plugin. Here is an example configuration for the ``ssh_exfil``
plugin:

.. code-block:: yaml

   _version: '1.0'
   base: /home/mattg/cdc/isu1-18
   project: ISU1-18
   flags: []
   post:
   - service: WWW SSH
       commands:
       - ssh_exfil:
           files:
               - /root/ToughNut/

The above configuration explicitly declares that the service ``WWW SSH`` should use the
``ssh_exfil`` plugin, and should look for additional files in the ``/root/ToughNut`` directory.
Any additional services exposing SSH will automatically attempt to find any of the default exfil
files.

Plugins
-------

SSH Exfil
^^^^^^^^^

.. autoclass:: flag_slurper.autolib.post.SSHFileExfil

Custom Plugins
--------------
:term:`CDCs <CDC>` often have unique elements that AutoPWN doesn't know how to exploit. Frequently
this includes services runing in a non-standard way, and interesting ways to gain access to the
system. For this reason, AutoPWN allows you to write custom Post PWN plugins, to do any post
actions that are necessary for your targets. To write a plugin, you must subclass
:py:class:`~flag_slurper.autolib.post.PostPlugin` and register it with the
:py:class:`~flag_slurper.autolib.post.PluginRegistry`.

.. autoclass:: flag_slurper.autolib.post.PostPlugin
   :members:

.. autoclass:: flag_slurper.autolib.post.PluginRegistry
   :members:

Loading Custom Plugins
----------------------
Currently, post pwn plugins do not have an auto-loading method (i.e. entry points). In order to
load a custom plugins, you must manually call :py:func:`~flag_slurper.autolib.post.PluginRegistry.register`
after ensuring your plugin is on the ``PYTHONPATH``. A much better method is planned.
