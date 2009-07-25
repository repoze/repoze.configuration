.. _import_api:

Import-Level API
----------------

Here is the import-level API for repoze.configuration:

.. automodule:: repoze.configuration

  .. autoclass:: ConfigurationError

  .. autoclass:: ConfigurationConflict

  .. autofunction:: load

  .. autofunction:: execute

.. _declaration_api:

Declaration API
---------------

.. automodule:: repoze.configuration.declaration

  .. autoclass:: YAMLDeclaration
     :members: action, expect, resolve, error, boolean, string, integer, getvalue, call_later

